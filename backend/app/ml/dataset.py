"""Synthetic event-cost dataset generator.

IMPORTANT / HONESTY NOTE
------------------------
No openly licensed public dataset of real-world event costs with the feature
granularity this project needs (category x guest count x city tier x venue x
duration x service tiers) could be identified for use here. Rather than scrape
vendor websites (licensing unclear) or silently present invented numbers as
market data, this module generates a **clearly labelled synthetic dataset**
from transparent, documented cost rules.

Every rule below is an explicit, auditable formula. The generated rows are
therefore *internally consistent* and useful for demonstrating that the ML
pipeline learns real signal, but the evaluation metrics reported by this
project measure **fit to the synthetic generating process**, NOT accuracy
against real market prices. Anything the UI says about cost must carry that
caveat.

Cost model (all amounts in INR, the dataset currency)::

    catering    = guests * per_guest(catering_level) * city_mult(city)
    venue       = venue_base(venue_type) * city_mult(city) * (duration / 5)
    decoration  = deco_base(decoration_level) * (1 + guests / 300)
    photography = photo_base(photography)
    fixed_block = (venue + decoration + photography) * event_type_mult
    subtotal    = catering + fixed_block
    total       = (subtotal + 0.08 * subtotal) * lognormal_noise(sigma=0.12)
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.schemas.vocabulary import (
    CATERING_LEVELS,
    CITY_TIERS,
    DECORATION_LEVELS,
    EVENT_TYPES,
    PHOTOGRAPHY_LEVELS,
    VENUE_TYPES,
)

CURRENCY = "INR"

# --- rule tables ------------------------------------------------------------
BASE_CATERING_PER_GUEST = {"basic": 450.0, "standard": 900.0, "premium": 1800.0}
CITY_COST_MULTIPLIER = {"tier1_metro": 1.35, "tier2_city": 1.0, "tier3_town": 0.7}

VENUE_BASE = {
    "banquet_hall": 40_000.0,
    "hotel": 90_000.0,
    "outdoor_garden": 35_000.0,
    "farmhouse": 45_000.0,
    "banquet_resort": 120_000.0,
    "home": 10_000.0,
}

DECORATION_BASE = {"basic": 15_000.0, "standard": 45_000.0, "premium": 120_000.0}
PHOTO_BASE = {"basic": 8_000.0, "standard": 25_000.0, "premium": 60_000.0}

# Multiplier applied to the venue+decor+photo block only; catering is driven
# by guests and menu tier.
EVENT_TYPE_FIXED_MULTIPLIER = {
    "wedding": 1.45,
    "birthday": 0.85,
    "anniversary": 1.05,
    "corporate": 1.25,
    "college": 0.95,
    "community": 0.8,
}

EXTRAS_RATE = 0.08
NOISE_SIGMA = 0.12
REFERENCE_DURATION = 5.0

COST_FEATURE_COLUMNS = [
    "event_type",
    "guest_count",
    "city",
    "venue_type",
    "duration_hours",
    "catering_level",
    "decoration_level",
    "photography",
]

COST_NUMERIC_FEATURES = ["guest_count", "duration_hours"]
COST_CATEGORICAL_FEATURES = [
    "event_type",
    "city",
    "venue_type",
    "catering_level",
    "decoration_level",
    "photography",
]


def compute_catering(guests: int, catering_level: str, city: str) -> float:
    return guests * BASE_CATERING_PER_GUEST[catering_level] * CITY_COST_MULTIPLIER[city]


def compute_venue(venue_type: str, city: str, duration_hours: int) -> float:
    return (
        VENUE_BASE[venue_type]
        * CITY_COST_MULTIPLIER[city]
        * (duration_hours / REFERENCE_DURATION)
    )


def compute_decoration(decoration_level: str, guests: int) -> float:
    return DECORATION_BASE[decoration_level] * (1 + guests / 300)


def compute_photography(photography: str) -> float:
    return PHOTO_BASE[photography]


def compute_total_cost(
    *,
    event_type: str,
    guest_count: int,
    city: str,
    venue_type: str,
    duration_hours: int,
    catering_level: str,
    decoration_level: str,
    photography: str,
) -> dict[str, float]:
    """Pure function version of the cost rules — used by tests and the app.

    The returned component values are the *event-type adjusted* amounts, so
    they always sum exactly to ``total``. Callers can therefore present the
    breakdown without any residual or unallocated remainder.
    """
    catering = compute_catering(guest_count, catering_level, city)
    multiplier = EVENT_TYPE_FIXED_MULTIPLIER[event_type]

    # The event-type multiplier scales the fixed block (venue, decor, photo)
    # but not catering, which is driven by guests and menu tier.
    venue = compute_venue(venue_type, city, duration_hours) * multiplier
    decoration = compute_decoration(decoration_level, guest_count) * multiplier
    photo = compute_photography(photography) * multiplier

    subtotal = catering + venue + decoration + photo
    extras = subtotal * EXTRAS_RATE
    return {
        "catering": catering,
        "venue": venue,
        "decoration": decoration,
        "photography": photo,
        "fixed_block": venue + decoration + photo,
        "extras": extras,
        "total": subtotal + extras,
    }


def generate_cost_dataset(n_rows: int = 4000, seed: int = 42) -> pd.DataFrame:
    """Generate a labelled synthetic cost dataset.

    Sampling is deliberately *not* uniform across every combination: guest
    counts follow a log-normal (most events are small-to-mid sized) and the
    tier/level choices are weighted so the training distribution resembles
    how people actually plan events.
    """
    rng = np.random.default_rng(seed)

    def pick(options: list[str], weights: list[float]) -> str:
        return str(rng.choice(options, p=weights))

    event_weights = [0.30, 0.22, 0.13, 0.13, 0.13, 0.09]
    city_weights = [0.45, 0.35, 0.20]
    venue_weights = [0.32, 0.20, 0.16, 0.16, 0.10, 0.06]
    level_weights = [0.25, 0.52, 0.23]

    rows: list[dict[str, Any]] = []
    for _ in range(n_rows):
        event_type = pick(EVENT_TYPES, event_weights)
        city = pick(CITY_TIERS, city_weights)
        venue_type = pick(VENUE_TYPES, venue_weights)
        catering_level = pick(CATERING_LEVELS, level_weights)
        decoration_level = pick(DECORATION_LEVELS, level_weights)
        photography = pick(PHOTOGRAPHY_LEVELS, level_weights)

        # Log-normal guest counts clipped to a realistic 10..1200 range.
        guests = int(np.clip(rng.lognormal(mean=4.35, sigma=0.75), 10, 1200))
        duration = int(rng.choice([3, 4, 5, 6, 8], p=[0.10, 0.20, 0.34, 0.24, 0.12]))

        breakdown = compute_total_cost(
            event_type=event_type,
            guest_count=guests,
            city=city,
            venue_type=venue_type,
            duration_hours=duration,
            catering_level=catering_level,
            decoration_level=decoration_level,
            photography=photography,
        )
        noise = float(rng.lognormal(mean=0.0, sigma=NOISE_SIGMA))
        total = breakdown["total"] * noise

        rows.append(
            {
                "event_type": event_type,
                "guest_count": guests,
                "city": city,
                "venue_type": venue_type,
                "duration_hours": duration,
                "catering_level": catering_level,
                "decoration_level": decoration_level,
                "photography": photography,
                "cost_catering": round(breakdown["catering"], 2),
                "cost_venue": round(breakdown["venue"], 2),
                "cost_decoration": round(breakdown["decoration"], 2),
                "cost_photography": round(breakdown["photography"], 2),
                "cost_extras": round(breakdown["extras"], 2),
                "total_cost": round(total, 2),
                "currency": CURRENCY,
            }
        )

    return pd.DataFrame(rows)


DATASET_NOTE = (
    "SYNTHETIC dataset generated from transparent cost rules (see "
    "backend/app/ml/dataset.py). Metrics describe fit to these rules, not "
    "real-world market accuracy. Treat estimates as directional planning "
    "figures and confirm with actual vendor quotes."
)

