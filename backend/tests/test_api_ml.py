"""Tests for the three ML models exposed through the API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


COST_REQUEST = {
    "event_type": "wedding",
    "guest_count": 250,
    "city": "tier1_metro",
    "venue_type": "hotel",
    "duration_hours": 6,
    "catering_level": "premium",
    "decoration_level": "premium",
    "photography": "premium",
    "budget": 1_500_000,
}


def test_cost_prediction(client: TestClient) -> None:
    response = client.post("/api/ml/predict-cost", json=COST_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_cost"] > 0
    assert body["lower_bound"] <= body["predicted_cost"] <= body["upper_bound"]
    assert body["per_guest_cost"] > 0
    assert body["budget_status"] in {"within_budget", "over_budget"}
    assert body["feature_importances"]
    # The synthetic-data caveat must always be surfaced.
    assert "SYNTHETIC" in body["data_note"]


def test_cost_prediction_scales_with_guests(client: TestClient) -> None:
    small = client.post(
        "/api/ml/predict-cost", json={**COST_REQUEST, "guest_count": 50}
    ).json()
    large = client.post(
        "/api/ml/predict-cost", json={**COST_REQUEST, "guest_count": 500}
    ).json()
    assert large["predicted_cost"] > small["predicted_cost"]


def test_cost_prediction_without_budget(client: TestClient) -> None:
    payload = {k: v for k, v in COST_REQUEST.items() if k != "budget"}
    response = client.post("/api/ml/predict-cost", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["budget_status"] == "no_budget"
    assert body["budget"] is None


def test_recommendations(client: TestClient) -> None:
    response = client.post(
        "/api/ml/recommend",
        json={
            "event_type": "wedding",
            "budget": 1_200_000,
            "guest_count": 250,
            "preferences": ["outdoor", "garden", "floral"],
            "style": "Classic",
            "top_k": 6,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["recommendations"]) == 6
    assert [r["rank"] for r in body["recommendations"]] == [1, 2, 3, 4, 5, 6]
    for rec in body["recommendations"]:
        assert rec["name"]
        assert rec["reason"]
        assert 0.0 <= rec["score"] <= 1.0
    assert "content-based" in body["method_note"].lower()


def test_recommendations_respect_preferences(client: TestClient) -> None:
    """A request that names 'garden' should surface a garden-related item."""
    response = client.post(
        "/api/ml/recommend",
        json={
            "event_type": "wedding",
            "budget": 900_000,
            "guest_count": 200,
            "preferences": ["garden", "outdoor"],
            "style": "Classic",
            "top_k": 10,
        },
    )
    assert response.status_code == 200
    names = [r["name"] for r in response.json()["recommendations"]]
    assert any("Garden" in n or "Rustic" in n or "Floral" in n for n in names)


def test_budget_risk_high(client: TestClient) -> None:
    response = client.post(
        "/api/ml/budget-risk",
        json={
            "budget": 100_000,
            "predicted_cost": 900_000,
            "contingency_pct": 10,
            "guest_count": 200,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "high"
    assert body["reasons"]
    assert body["saving_tips"]
    assert body["assumptions"]
    assert body["suggested_contingency"] > 0


def test_budget_risk_low(client: TestClient) -> None:
    response = client.post(
        "/api/ml/budget-risk",
        json={
            "budget": 5_000_000,
            "predicted_cost": 900_000,
            "contingency_pct": 10,
            "guest_count": 200,
        },
    )
    assert response.status_code == 200
    assert response.json()["risk_level"] == "low"


def test_budget_risk_medium(client: TestClient) -> None:
    response = client.post(
        "/api/ml/budget-risk",
        json={
            "budget": 1_020_000,
            "predicted_cost": 900_000,
            "contingency_pct": 10,
            "guest_count": 200,
        },
    )
    assert response.status_code == 200
    assert response.json()["risk_level"] == "medium"


def test_ml_metrics_expose_all_three_models(client: TestClient) -> None:
    response = client.get("/api/ml/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["cost_model"]["model"] == "RandomForestRegressor"
    assert "r2" in body["cost_model"]
    assert "NearestNeighbors" in body["recommendation_model"]["model"]
    assert body["risk_model"]["model"] == "DecisionTreeClassifier"
    assert "accuracy" in body["risk_model"]
    assert body["generated_at"]
    assert "SYNTHETIC" in body["dataset_note"]


@pytest.mark.parametrize(
    "payload",
    [
        {**COST_REQUEST, "guest_count": 0},
        {**COST_REQUEST, "duration_hours": 7},
    ],
)
def test_cost_prediction_validation(client: TestClient, payload: dict) -> None:
    assert client.post("/api/ml/predict-cost", json=payload).status_code == 422
