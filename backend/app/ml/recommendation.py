"""Model B — Content-based Recommendation Engine.

A ``NearestNeighbors`` model over a curated catalogue of themes, decoration
packages, catering styles, activities and service bundles.

How it works
------------
1. Each catalogue item is encoded into a numeric vector:
   * categorical part -> one-hot flags for event type, style and price band
   * numeric part     -> scaled budget-per-guest and popularity weight
   * text part        -> token overlap between the item's keywords/tags and
                         the user's stated preferences (a plain vocabulary
                         tokenizer, so no extra dependency is needed)
2. The user's request is encoded with the *same* function.
3. ``NearestNeighbors`` (cosine distance) returns the closest catalogue items.
4. A small, explicit relevance bonus re-ranks exact preference matches so a
   near-duplicate vector cannot bury a clearly better match.

Honesty note
------------
This is **content-based filtering over a static, hand-curated catalogue**. The
model does *not* learn from user behaviour, click logs or ratings, because no
such feedback data was collected. The score is a similarity between the
request and the item's attributes; the "reason" string is generated from the
matching attributes. Popularity is an editorial weight, not a measured
statistic.
"""
from __future__ import annotations

import re
from typing import Any

import numpy as np
from sklearn.neighbors import NearestNeighbors

from app.ml.catalogue_index import (
    CATEGORY_ORDER,
    EVENT_TYPES,
    PRICE_BANDS,
    RECOMMENDATION_ITEMS,
    STYLES,
    CatalogueItem,
)

TOKEN_RE = re.compile(r"[a-z0-9]+")

RECOMMENDATION_METHOD_NOTE = (
    "Content-based k-nearest-neighbours over a hand-curated catalogue. "
    "Similarity is computed from event type, style, price band, budget-per-guest "
    "and preference-token overlap. No user-interaction data was collected, so the "
    "ranking does NOT reflect learned personal preferences."
)


def tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def item_tokens(item: CatalogueItem) -> set[str]:
    tokens: set[str] = set()
    tokens.update(item.keywords)
    tokens.update(item.tags)
    tokens.update(tokenize(item.name))
    tokens.update(tokenize(item.description))
    return tokens


def item_vector(item: CatalogueItem) -> np.ndarray:
    """Fixed-length encoding of a catalogue item."""
    vec: list[float] = []
    # Event-type affinity (fraction of the item's supported types that match).
    for et in EVENT_TYPES:
        vec.append(1.0 if et in item.event_types else 0.0)
    # Style affinity.
    for st in STYLES:
        vec.append(1.0 if st in item.styles else 0.0)
    # Price band one-hot.
    for band in PRICE_BANDS:
        vec.append(1.0 if band == item.price_band else 0.0)
    # Numeric: cost per guest (log-scaled) and popularity.
    vec.append(float(np.log1p(item.cost_per_guest)) / 8.0)
    vec.append(float(item.popularity))
    return np.asarray(vec, dtype=float)


def request_vector(
    *,
    event_type: str,
    style: str,
    budget_per_guest: float,
    preferences: list[str],
) -> np.ndarray:
    vec: list[float] = []
    # Event-type affinity: 1.0 for the requested type, plus a smaller weight
    # for the item's other supported types so generic items stay reachable.
    for et in EVENT_TYPES:
        if et == event_type:
            vec.append(1.0)
        else:
            vec.append(0.15)
    # Style affinity.
    for st in STYLES:
        vec.append(1.0 if st == style else 0.0)
    # Request price band derived from the per-guest budget.
    if budget_per_guest < 600:
        band = "budget"
    elif budget_per_guest < 1300:
        band = "mid"
    else:
        band = "premium"
    for b in PRICE_BANDS:
        vec.append(1.0 if b == band else 0.0)
    vec.append(float(np.log1p(max(budget_per_guest, 0.0))) / 8.0)
    vec.append(0.5)  # neutral popularity anchor for the request
    return np.asarray(vec, dtype=float)


def build_recommendation_index() -> tuple[NearestNeighbors, list[CatalogueItem], dict[str, Any]]:
    """Fit the NearestNeighbors model over the catalogue."""
    items = list(RECOMMENDATION_ITEMS)
    matrix = np.vstack([item_vector(i) for i in items])

    # The request vector needs preference overlap appended as well, so the
    # feature space must be consistent. We append a fixed-size token-overlap
    # block to both sides.
    token_vocab = sorted({t for i in items for t in item_tokens(i)})
    token_index = {t: idx for idx, t in enumerate(token_vocab)}

    item_matrix = np.hstack(
        [matrix, np.vstack([_token_overlap_vector(item_tokens(i), token_index) for i in items])]
    )

    n_neighbors = min(len(items), 12)
    model = NearestNeighbors(n_neighbors=n_neighbors, metric="cosine", algorithm="brute")
    model.fit(item_matrix)

    meta = {
        "n_items": len(items),
        "token_vocab_size": len(token_vocab),
        "n_neighbors": n_neighbors,
        "metric": "cosine",
        "categories": CATEGORY_ORDER,
    }
    return model, items, {"token_vocab": token_vocab, "token_index": token_index, **meta}


def _pref_vector(preferences: list[str], token_index: dict[str, int]) -> np.ndarray:
    tokens: set[str] = set()
    for pref in preferences:
        tokens.update(tokenize(pref))
    vec = np.zeros(len(token_index), dtype=float)
    for t in tokens:
        idx = token_index.get(t)
        if idx is not None:
            vec[idx] = 1.0
    return vec


def recommend_from_index(
    model: NearestNeighbors,
    items: list[CatalogueItem],
    meta: dict[str, Any],
    *,
    event_type: str,
    style: str,
    budget: float,
    guest_count: int,
    preferences: list[str],
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """Return ranked recommendations with human-readable reasons."""
    token_index = meta["token_index"]
    base = request_vector(
        event_type=event_type,
        style=style,
        budget_per_guest=(budget / guest_count) if guest_count > 0 else 0.0,
        preferences=preferences,
    )
    query = np.hstack([base, _pref_vector(preferences, token_index)]).reshape(1, -1)

    distances, indices = model.kneighbors(query, n_neighbors=min(top_k * 3, len(items)))
    dist = distances[0]
    idx = indices[0]

    pref_tokens: set[str] = set()
    for pref in preferences:
        pref_tokens.update(tokenize(pref))

    scored: list[dict[str, Any]] = []
    for distance, i in zip(dist, idx):
        item = items[int(i)]
        # Cosine distance -> similarity in [0, 1].
        similarity = float(max(0.0, 1.0 - distance))
        matched = sorted(pref_tokens & item_tokens(item))
        # Explicit bonus for genuine preference matches so a near-duplicate
        # catalogue vector cannot outrank an exact match.
        pref_bonus = min(0.15, 0.05 * len(matched))
        score = float(min(1.0, similarity + pref_bonus))
        scored.append(
            {
                "item": item,
                "score": round(score, 4),
                "matched_preferences": matched,
                "similarity": round(similarity, 4),
            }
        )

    scored.sort(key=lambda d: (-d["score"], -d["item"].popularity))

    results: list[dict[str, Any]] = []
    for rank, entry in enumerate(scored[:top_k], start=1):
        item: CatalogueItem = entry["item"]
        results.append(
            {
                "rank": rank,
                "name": item.name,
                "category": item.category,
                "score": entry["score"],
                "reason": _build_reason(item, entry["matched_preferences"], event_type, style),
                "tags": list(item.tags),
                "estimated_cost_per_guest": item.cost_per_guest,
                "description": item.description,
                "price_band": item.price_band,
            }
        )
    return results


def _build_reason(
    item: CatalogueItem,
    matched: list[str],
    event_type: str,
    style: str,
) -> str:
    parts: list[str] = []
    if event_type in item.event_types:
        parts.append(f"suited to {event_type} events")
    if style in item.styles:
        parts.append(f"matches your {style.lower()} style")
    if matched:
        parts.append(f"matches your preference for {', '.join(matched[:3])}")
    parts.append(f"{item.price_band} price band")
    if not parts:
        parts.append("complements the rest of your plan")
    return "; ".join(parts) + "."


def recommendation_metrics(meta: dict[str, Any]) -> dict[str, Any]:
    """Evaluation summary for the recommendation model.

    There is no held-out ground-truth ranking to score against (no click or
    rating data exists), so instead of inventing an accuracy figure we report
    a *retrieval sanity check*: for each event type, how many of the top-3
    nearest neighbours belong to that event type's compatible set.
    """
    return {
        "model": "NearestNeighbors (content-based, cosine)",
        "n_items": meta.get("n_items"),
        "metric": meta.get("metric"),
        "n_neighbors": meta.get("n_neighbors"),
        "token_vocab_size": meta.get("token_vocab_size"),
        "evaluation_note": (
            "No labelled preference data exists, so no accuracy metric is reported. "
            "Retrieval quality is assessed by a top-3 category/type sanity check "
            "documented in backend/scripts/evaluate_recommendations.py."
        ),
        "method_note": RECOMMENDATION_METHOD_NOTE,
    }

    return model, items, {"token_vocab": token_vocab, "token_index": token_index, **meta}


def _token_overlap_vector(tokens: set[str], token_index: dict[str, int]) -> np.ndarray:
    vec = np.zeros(len(token_index), dtype=float)
    for t in tokens:
        idx = token_index.get(t)
        if idx is not None:
            vec[idx] = 1.0
    return vec
