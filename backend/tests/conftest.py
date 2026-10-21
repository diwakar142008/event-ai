"""Shared pytest fixtures.

Tests run against an isolated temporary SQLite database so they never touch
the developer's ``eventora.db``.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway database *before* the app modules import.
_TMP_DB = Path(tempfile.gettempdir()) / "eventora_test.db"
if _TMP_DB.exists():
    _TMP_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"
os.environ["AI_PROVIDER"] = "none"
os.environ["ML_MODEL_DIR"] = str(
    Path(__file__).resolve().parent.parent / "ml_artifacts"
)

from fastapi.testclient import TestClient  # noqa: E402

from app.database.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _prepare_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_event_payload() -> dict:
    return {
        "name": "Meera & Arjun Wedding",
        "event_type": "wedding",
        "event_date": "2027-02-14",
        "city": "tier1_metro",
        "guest_count": 250,
        "budget": 1_500_000,
        "theme": "Elegant",
        "style": "Classic",
        "preferences": ["outdoor ceremony", "live music", "vegetarian"],
        "venue_type": "hotel",
        "duration_hours": 6,
        "catering_level": "premium",
        "decoration_level": "premium",
        "photography": "premium",
    }
