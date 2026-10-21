"""End-to-end API tests covering the full Eventora workflow."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_reports_models_and_database(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"
    assert body["models_loaded"]["cost_model"] is True
    assert body["models_loaded"]["risk_model"] is True


def test_vocabulary_endpoint_lists_all_options(client: TestClient) -> None:
    response = client.get("/api/vocabulary")
    assert response.status_code == 200
    body = response.json()
    assert len(body["event_types"]) == 6
    assert "tier1_metro" in [c["value"] for c in body["city_tiers"]]
    assert body["currency"] == "INR"


def test_event_lifecycle(client: TestClient, sample_event_payload: dict) -> None:
    # Create
    response = client.post("/api/events", json=sample_event_payload)
    assert response.status_code == 201
    event = response.json()
    event_id = event["id"]
    assert event["preferences"] == sample_event_payload["preferences"]

    # Read
    response = client.get(f"/api/events/{event_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["name"] == sample_event_payload["name"]
    assert detail["plan"] is None

    # Update
    response = client.patch(f"/api/events/{event_id}", json={"guest_count": 300})
    assert response.status_code == 200
    assert response.json()["guest_count"] == 300

    # List
    response = client.get("/api/events")
    assert response.status_code == 200
    assert any(e["id"] == event_id for e in response.json())

    # Delete
    response = client.delete(f"/api/events/{event_id}")
    assert response.status_code == 204
    assert client.get(f"/api/events/{event_id}").status_code == 404


def test_event_validation_rejects_bad_values(client: TestClient, sample_event_payload: dict) -> None:
    payload = {**sample_event_payload, "event_type": "not-a-real-type"}
    response = client.post("/api/events", json=payload)
    assert response.status_code == 422


def test_event_validation_rejects_zero_guests(client: TestClient, sample_event_payload: dict) -> None:
    payload = {**sample_event_payload, "guest_count": 0}
    response = client.post("/api/events", json=payload)
    assert response.status_code == 422


def test_missing_event_returns_404(client: TestClient) -> None:
    assert client.get("/api/events/does-not-exist").status_code == 404


def test_generate_plan_creates_workspace(client: TestClient, sample_event_payload: dict) -> None:
    event_id = client.post("/api/events", json=sample_event_payload).json()["id"]

    response = client.post("/api/ai/plan", json={"event_id": event_id})
    assert response.status_code == 200
    body = response.json()
    # No API key is configured in tests, so the deterministic fallback runs.
    assert body["source"] == "fallback"
    assert body["provider"] == "none"
    assert body["model"] == "deterministic-planner"
    assert "deterministic planner" in body["notice"].lower()

    plan = body["plan"]
    assert plan["overview"]["theme"] == "Elegant"
    assert len(plan["checklist"]) >= 20
    assert len(plan["timeline"]) >= 15
    assert len(plan["event_day_schedule"]) == 6
    assert plan["budget_breakdown"]
    assert plan["tips"]

    # The plan should be persisted and seed the working checklist/timeline.
    detail = client.get(f"/api/events/{event_id}").json()
    assert detail["plan"] is not None
    assert detail["plan_source"] == "fallback"
    assert len(detail["checklist"]) >= 20
    assert len(detail["timeline"]) >= 15
    assert len(detail["expenses"]) == 5


def test_plan_generation_requires_an_event(client: TestClient) -> None:
    response = client.post("/api/ai/plan", json={})
    assert response.status_code == 400


def test_chat_uses_deterministic_fallback(client: TestClient, sample_event_payload: dict) -> None:
    event_id = client.post("/api/events", json=sample_event_payload).json()["id"]
    response = client.post(
        "/api/ai/chat", json={"event_id": event_id, "message": "How much will this cost?"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "fallback"
    assert "INR" in body["reply"]
