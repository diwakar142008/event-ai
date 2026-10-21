"""Unit tests for the ML pipelines and the deterministic planner."""
from __future__ import annotations

import pytest

from app.ml.dataset import compute_total_cost, generate_cost_dataset
from app.ml.recommendation import build_recommendation_index, recommend_from_index
from app.ml.risk import build_risk_dataset, label_risk, risk_features


# --------------------------------------------------------------------------- #
# Cost model
# --------------------------------------------------------------------------- #
def test_dataset_generation_is_deterministic() -> None:
    a = generate_cost_dataset(n_rows=200, seed=7)
    b = generate_cost_dataset(n_rows=200, seed=7)
    assert a.equals(b)


def test_dataset_has_expected_shape_and_positive_costs() -> None:
    df = generate_cost_dataset(n_rows=500, seed=3)
    assert len(df) == 500
    assert (df["total_cost"] > 0).all()
    assert df["guest_count"].between(10, 1200).all()
    assert set(df["event_type"]) <= {
        "wedding",
        "birthday",
        "anniversary",
        "corporate",
        "college",
        "community",
    }


def test_cost_increases_with_guest_count() -> None:
    base = dict(
        event_type="wedding",
        city="tier1_metro",
        venue_type="hotel",
        duration_hours=5,
        catering_level="premium",
        decoration_level="premium",
        photography="premium",
    )
    small = compute_total_cost(guest_count=50, **base)["total"]
    large = compute_total_cost(guest_count=500, **base)["total"]
    assert large > small


def test_cost_increases_with_city_tier() -> None:
    base = dict(
        event_type="wedding",
        guest_count=200,
        venue_type="hotel",
        duration_hours=5,
        catering_level="standard",
        decoration_level="standard",
        photography="standard",
    )
    metro = compute_total_cost(city="tier1_metro", **base)["total"]
    town = compute_total_cost(city="tier3_town", **base)["total"]
    assert metro > town


def test_cost_increases_with_duration() -> None:
    base = dict(
        event_type="wedding",
        guest_count=200,
        city="tier2_city",
        venue_type="hotel",
        catering_level="standard",
        decoration_level="standard",
        photography="standard",
    )
    short = compute_total_cost(duration_hours=3, **base)["total"]
    long = compute_total_cost(duration_hours=8, **base)["total"]
    assert long > short


def test_total_cost_equals_sum_of_components() -> None:
    parts = compute_total_cost(
        event_type="birthday",
        guest_count=80,
        city="tier2_city",
        venue_type="banquet_hall",
        duration_hours=4,
        catering_level="standard",
        decoration_level="basic",
        photography="basic",
    )
    expected = (
        parts["catering"]
        + parts["venue"]
        + parts["decoration"]
        + parts["photography"]
        + parts["extras"]
    )
    assert parts["total"] == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Risk model
# --------------------------------------------------------------------------- #
def test_label_risk_thresholds() -> None:
    # 1.5x coverage -> low
    assert label_risk(1_500_000, 1_000_000, 0) == "low"
    # 1.1x coverage -> medium
    assert label_risk(1_100_000, 1_000_000, 0) == "medium"
    # 0.8x coverage -> high
    assert label_risk(800_000, 1_000_000, 0) == "high"


def test_label_risk_accounts_for_contingency() -> None:
    """A budget that only covers the base estimate can become high-risk once
    a contingency allowance is applied.

    Note that a coverage ratio of exactly 1.0 is the documented lower edge of
    the "medium" band, so a budget that exactly matches the estimate is medium
    risk, not low risk.
    """
    assert label_risk(1_000_000, 1_000_000, 0) == "medium"
    assert label_risk(1_000_000, 1_000_000, 20) == "high"
    # A clearly healthy buffer stays low even with a contingency applied.
    assert label_risk(1_500_000, 1_000_000, 20) == "low"


def test_risk_features_are_consistent() -> None:
    feats = risk_features(2_000_000, 1_000_000, 10, 100)
    assert feats["coverage_ratio"] == pytest.approx(2_000_000 / 1_100_000)
    assert feats["slack_amount"] == pytest.approx(900_000)
    assert feats["guest_cost_ratio"] == pytest.approx(10_000)


def test_risk_dataset_covers_all_three_classes() -> None:
    df = build_risk_dataset(n_rows=1500, seed=11)
    assert set(df["risk_label"]) == {"low", "medium", "high"}
    assert (df["coverage_ratio"] > 0).all()


# --------------------------------------------------------------------------- #
# Recommendation model
# --------------------------------------------------------------------------- #
def test_recommendation_index_is_built_over_all_items() -> None:
    model, items, meta = build_recommendation_index()
    assert len(items) == meta["n_items"]
    assert model.n_samples_fit_ == len(items)


def test_recommendations_prefer_matching_event_type() -> None:
    model, items, meta = build_recommendation_index()
    results = recommend_from_index(
        model,
        items,
        meta,
        event_type="corporate",
        style="Modern",
        budget=1_000_000,
        guest_count=200,
        preferences=[],
        top_k=8,
    )
    assert results
    assert any(r["category"] == "theme" for r in results)


def test_recommendation_scores_are_sorted_descending() -> None:
    model, items, meta = build_recommendation_index()
    results = recommend_from_index(
        model,
        items,
        meta,
        event_type="wedding",
        style="Classic",
        budget=2_000_000,
        guest_count=300,
        preferences=["floral"],
        top_k=10,
    )
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_recommendations_are_deterministic() -> None:
    model, items, meta = build_recommendation_index()
    kwargs = dict(
        event_type="birthday",
        style="Festive",
        budget=300_000,
        guest_count=60,
        preferences=["music", "dance"],
        top_k=5,
    )
    first = recommend_from_index(model, items, meta, **kwargs)
    second = recommend_from_index(model, items, meta, **kwargs)
    assert [r["name"] for r in first] == [r["name"] for r in second]


def test_recommendation_top_k_is_respected() -> None:
    model, items, meta = build_recommendation_index()
    results = recommend_from_index(
        model,
        items,
        meta,
        event_type="wedding",
        style="Luxury",
        budget=5_000_000,
        guest_count=500,
        preferences=[],
        top_k=3,
    )
    assert len(results) == 3


# --------------------------------------------------------------------------- #
# Deterministic planner
# --------------------------------------------------------------------------- #
def _sample_event() -> dict:
    return {
        "name": "Test Event",
        "event_type": "wedding",
        "event_date": "2027-05-01",
        "city": "tier2_city",
        "guest_count": 120,
        "budget": 800_000,
        "theme": "Elegant",
        "style": "Classic",
        "preferences": [],
        "venue_type": "banquet_hall",
        "duration_hours": 5,
        "catering_level": "standard",
        "decoration_level": "standard",
        "photography": "standard",
    }


def test_deterministic_plan_is_stable() -> None:
    from app.services.planner import generate_deterministic_plan

    event = _sample_event()
    first = generate_deterministic_plan(event)
    second = generate_deterministic_plan(event)
    assert first == second
    assert first["overview"]["theme"] == "Elegant"
    assert len(first["checklist"]) >= 20
    assert len(first["timeline"]) >= 15
    assert first["budget_breakdown"]


def test_deterministic_plan_satisfies_the_schema() -> None:
    from app.schemas.plan import EventPlanSchema
    from app.services.planner import generate_deterministic_plan

    event = {
        **_sample_event(),
        "event_type": "birthday",
        "city": "tier3_town",
        "guest_count": 40,
        "budget": 150_000,
        "theme": "Retro Disco",
        "style": "Festive",
        "venue_type": "home",
        "duration_hours": 3,
        "catering_level": "basic",
        "decoration_level": "basic",
        "photography": "basic",
    }
    plan = generate_deterministic_plan(event)
    plan.pop("_meta", None)
    validated = EventPlanSchema.model_validate(plan)
    assert validated.overview.theme == "Retro Disco"
    assert validated.budget_breakdown


def test_deterministic_plan_schedule_scales_with_duration() -> None:
    from app.services.planner import generate_deterministic_plan

    short = generate_deterministic_plan({**_sample_event(), "duration_hours": 3})
    long = generate_deterministic_plan({**_sample_event(), "duration_hours": 8})
    short_end = short["event_day_schedule"][-1]["end_time"]
    long_end = long["event_day_schedule"][-1]["end_time"]
    assert long_end > short_end
