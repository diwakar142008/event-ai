"""Machine-learning API routes — the three executable models."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.event import (
    BudgetRiskOut,
    BudgetRiskRequest,
    CostPredictionOut,
    CostPredictionRequest,
    MLMetricsOut,
    RecommendationOut,
    RecommendationRequest,
)
from app.services.ml_service import ModelNotTrainedError, model_store

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])


@router.post("/predict-cost", response_model=CostPredictionOut)
def predict_cost(payload: CostPredictionRequest) -> CostPredictionOut:
    """Model A — Random Forest cost prediction."""
    try:
        result = model_store.predict_cost(
            event_type=payload.event_type,
            guest_count=payload.guest_count,
            city=payload.city,
            venue_type=payload.venue_type,
            duration_hours=payload.duration_hours,
            catering_level=payload.catering_level,
            decoration_level=payload.decoration_level,
            photography=payload.photography,
            budget=payload.budget,
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CostPredictionOut.model_validate(result)


@router.post("/recommend", response_model=RecommendationOut)
def recommend(payload: RecommendationRequest) -> RecommendationOut:
    """Model B — content-based KNN recommendations."""
    try:
        result = model_store.recommend(
            event_type=payload.event_type,
            budget=payload.budget,
            guest_count=payload.guest_count,
            preferences=payload.preferences,
            style=payload.style,
            top_k=payload.top_k,
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RecommendationOut.model_validate(result)


@router.post("/budget-risk", response_model=BudgetRiskOut)
def budget_risk(payload: BudgetRiskRequest) -> BudgetRiskOut:
    """Model C — Decision Tree budget-risk classification."""
    try:
        result = model_store.assess_risk(
            budget=payload.budget,
            predicted_cost=payload.predicted_cost,
            contingency_pct=payload.contingency_pct,
            guest_count=payload.guest_count,
        )
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return BudgetRiskOut.model_validate(result)


@router.get("/metrics", response_model=MLMetricsOut)
def metrics() -> MLMetricsOut:
    """Reported evaluation metrics for all three models."""
    try:
        raw = model_store.metrics
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return MLMetricsOut.model_validate(
        {
            "cost_model": raw.get("cost_model", {}),
            "recommendation_model": raw.get("recommendation_model", {}),
            "risk_model": raw.get("risk_model", {}),
            "generated_at": raw.get("generated_at", ""),
            "dataset_note": raw.get("dataset_note", ""),
        }
    )
