"""Eventora AI — FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import ai, events, ml, workspace
from app.config import settings
from app.database.session import Base, engine
from app.schemas.event import ErrorOut, HealthOut

logger = logging.getLogger("eventora")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup so a fresh clone works without extra steps.
    Base.metadata.create_all(bind=engine)
    logger.info("Eventora AI %s started (environment=%s)", settings.version, settings.environment)
    yield
    engine.dispose()


app = FastAPI(
    title="Eventora AI — Smart Celebration Planner",
    description=(
        "Plan celebrations end to end: ML-driven cost estimation, content-based "
        "recommendations, budget-risk classification, and AI-assisted planning with "
        "a deterministic fallback when no LLM provider is configured."
    ),
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(workspace.router)
app.include_router(ml.router)
app.include_router(ai.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=ErrorOut(
            error="internal_server_error",
            message="An unexpected error occurred. Please try again.",
            details=None,
        ).model_dump(),
    )


@app.get("/api/health", response_model=HealthOut, tags=["system"])
def health() -> HealthOut:
    """Service health, including database and ML artifact status."""
    from app.services.ml_service import model_store

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {type(exc).__name__}"

    return HealthOut(
        status="ok" if db_status == "connected" else "degraded",
        version=settings.version,
        environment=settings.environment,
        ai_provider=settings.ai_provider,
        ai_configured=settings.ai_available,
        database=db_status,
        models_loaded=model_store.status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/vocabulary", tags=["system"])
def vocabulary() -> dict:
    """Controlled vocabularies used by the forms in the UI."""
    from app.schemas.vocabulary import (
        CATERING_LEVELS,
        CITY_TIERS,
        CITY_TIER_LABELS,
        DECORATION_LEVELS,
        DURATION_HOURS,
        EVENT_TYPES,
        EVENT_TYPE_LABELS,
        PHOTOGRAPHY_LEVELS,
        STYLES,
        THEMES,
        VENUE_TYPES,
        VENUE_TYPE_LABELS,
    )

    return {
        "event_types": [
            {"value": v, "label": EVENT_TYPE_LABELS[v]} for v in EVENT_TYPES
        ],
        "city_tiers": [
            {"value": v, "label": CITY_TIER_LABELS[v]} for v in CITY_TIERS
        ],
        "venue_types": [
            {"value": v, "label": VENUE_TYPE_LABELS[v]} for v in VENUE_TYPES
        ],
        "durations": DURATION_HOURS,
        "catering_levels": CATERING_LEVELS,
        "decoration_levels": DECORATION_LEVELS,
        "photography_levels": PHOTOGRAPHY_LEVELS,
        "styles": STYLES,
        "themes": THEMES,
        "currency": "INR",
    }
