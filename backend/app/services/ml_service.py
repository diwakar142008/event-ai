"""Inference wrappers around the trained joblib artifacts.

Models are loaded lazily once per process and cached. If artifacts are
missing the service raises a clear, actionable error telling the user to run
the training script — it never silently falls back to fake numbers.
"""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.ml.dataset import COST_FEATURE_COLUMNS, CURRENCY, DATASET_NOTE
from app.ml.recommendation import (
    RECOMMENDATION_METHOD_NOTE,
    build_recommendation_index,
    recommend_from_index,
)
from app.ml.risk import (
    LOW_RISK_COVERAGE,
    MEDIUM_RISK_COVERAGE,
    RISK_FEATURE_COLUMNS,
    RISK_LABEL_NOTE,
    risk_features,
)
from app.schemas.vocabulary import RISK_HIGH, RISK_LOW, RISK_MEDIUM, RISK_LABELS

_LOCK = Lock()


class ModelNotTrainedError(RuntimeError):
    """Raised when a model artifact is missing."""


class ModelStore:
    """Lazily-loaded container for the three trained models."""

    def __init__(self) -> None:
        self._cost_model: Any | None = None
        self._rec_model: Any | None = None
        self._rec_items: list[Any] | None = None
        self._rec_meta: dict[str, Any] | None = None
        self._risk_model: Any | None = None
        self._metrics: dict[str, Any] | None = None
        self._loaded = False

    # -- artifact paths ----------------------------------------------------
    @property
    def dir(self) -> Path:
        return settings.model_dir

    def _path(self, name: str) -> Path:
        return self.dir / name

    # -- loading -----------------------------------------------------------
    def load(self, force: bool = False) -> None:
        with _LOCK:
            if self._loaded and not force:
                return
            cost_path = self._path("cost_model.joblib")
            rec_path = self._path("recommendation_index.joblib")
            risk_path = self._path("budget_risk_model.joblib")
            metrics_path = self._path("metrics.json")

            if not cost_path.exists() or not risk_path.exists():
                raise ModelNotTrainedError(
                    "ML artifacts not found. Run: python -m app.ml.train --all"
                )

            self._cost_model = joblib.load(cost_path)
            self._risk_model = joblib.load(risk_path)

            if rec_path.exists():
                payload = joblib.load(rec_path)
                self._rec_model = payload["model"]
                self._rec_items = payload["items"]
                self._rec_meta = payload["meta"]
            else:
                # Rebuild in-memory from the curated catalogue if the artifact
                # is missing (deterministic — no fitting required).
                model, items, meta = build_recommendation_index()
                self._rec_model = model
                self._rec_items = items
                self._rec_meta = meta

            if metrics_path.exists():
                self._metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            else:
                self._metrics = {}

            self._loaded = True

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    @property
    def status(self) -> dict[str, bool]:
        return {
            "cost_model": (self.dir / "cost_model.joblib").exists(),
            "recommendation_model": (self.dir / "recommendation_index.joblib").exists(),
            "risk_model": (self.dir / "budget_risk_model.joblib").exists(),
        }

    @property
    def metrics(self) -> dict[str, Any]:
        self.ensure_loaded()
        return self._metrics or {}

    # -- Model A: cost prediction -----------------------------------------
    def predict_cost(
        self,
        *,
        event_type: str,
        guest_count: int,
        city: str,
        venue_type: str,
        duration_hours: int,
        catering_level: str,
        decoration_level: str,
        photography: str,
        budget: float | None = None,
    ) -> dict[str, Any]:
        self.ensure_loaded()
        if self._cost_model is None:
            raise ModelNotTrainedError("Cost model artifact missing.")

        row = {
            "event_type": event_type,
            "guest_count": int(guest_count),
            "city": city,
            "venue_type": venue_type,
            "duration_hours": int(duration_hours),
            "catering_level": catering_level,
            "decoration_level": decoration_level,
            "photography": photography,
        }
        # The pipeline was fitted on a DataFrame, so inference must use one too
        # (sklearn validates feature names and column order).
        frame = pd.DataFrame([row], columns=COST_FEATURE_COLUMNS)
        predicted = float(self._cost_model.predict(frame)[0])

        # Uncertainty band: derived from the model's own training RMSE, which
        # is a residual-based estimate rather than a confidence interval.
        rmse = float(self.metrics.get("cost_model", {}).get("rmse", 0.0) or 0.0)
        band = rmse if rmse > 0 else predicted * 0.15
        lower = max(0.0, predicted - band)
        upper = predicted + band

        metrics = self.metrics.get("cost_model", {})
        importances = metrics.get("feature_importances", {}) or {}

        result: dict[str, Any] = {
            "predicted_cost": round(predicted, 2),
            "currency": CURRENCY,
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
            "per_guest_cost": round(predicted / guest_count, 2) if guest_count else 0.0,
            "confidence_note": (
                f"Estimate from a Random Forest trained on {metrics.get('n_samples', 'n/a')} "
                f"synthetic cost records. Expected error is roughly +/- INR {round(band):,} "
                "(1x training RMSE). Use it as a planning range, not a quote."
            ),
            "feature_importances": importances,
            "data_note": DATASET_NOTE,
        }

        if budget is not None:
            gap = round(budget - predicted, 2)
            usage = round((predicted / budget) * 100, 1) if budget > 0 else None
            result.update(
                {
                    "budget": budget,
                    "budget_gap": gap,
                    "budget_usage_pct": usage,
                    "budget_status": "within_budget" if gap >= 0 else "over_budget",
                }
            )
        return result

    # -- Model B: recommendations -----------------------------------------
    def recommend(
        self,
        *,
        event_type: str,
        budget: float,
        guest_count: int,
        preferences: list[str],
        style: str,
        top_k: int = 8,
    ) -> dict[str, Any]:
        self.ensure_loaded()
        if self._rec_model is None or self._rec_items is None or self._rec_meta is None:
            raise ModelNotTrainedError("Recommendation index missing.")

        items = recommend_from_index(
            self._rec_model,
            self._rec_items,
            self._rec_meta,
            event_type=event_type,
            style=style,
            budget=budget,
            guest_count=guest_count,
            preferences=preferences,
            top_k=top_k,
        )
        per_guest = (budget / guest_count) if guest_count else 0.0
        explanation = (
            f"Ranked by content similarity to a {event_type} event with a "
            f"{style.lower()} style and an indicative budget of "
            f"INR {per_guest:,.0f} per guest. "
            + (
                f"Your stated preferences ({', '.join(preferences[:4])}) were matched "
                "against item tags and keywords."
                if preferences
                else "No explicit preferences were supplied, so ranking relies on "
                "event type, style and price band."
            )
        )
        return {
            "recommendations": items,
            "explanation": explanation,
            "method_note": RECOMMENDATION_METHOD_NOTE,
        }

    # -- Model C: budget risk ---------------------------------------------
    def assess_risk(
        self,
        *,
        budget: float,
        predicted_cost: float,
        contingency_pct: float,
        guest_count: int,
    ) -> dict[str, Any]:
        self.ensure_loaded()
        if self._risk_model is None:
            raise ModelNotTrainedError("Risk model artifact missing.")

        feats = risk_features(budget, predicted_cost, contingency_pct, guest_count)
        # Use a DataFrame so the column names match those seen during fitting
        # (sklearn warns when a bare ndarray is passed to a fitted estimator).
        vector = pd.DataFrame(
            [[feats[c] for c in RISK_FEATURE_COLUMNS]], columns=RISK_FEATURE_COLUMNS
        )
        risk_level = str(self._risk_model.predict(vector)[0])
        proba = self._risk_model.predict_proba(vector)[0]
        classes = list(self._risk_model.classes_)
        confidence = float(proba[classes.index(risk_level)]) if risk_level in classes else 0.0

        committed = predicted_cost * (1 + contingency_pct / 100)
        coverage = (budget / committed) if committed > 0 else 1.0
        slack = budget - committed

        reasons = self._build_reasons(risk_level, budget, predicted_cost, committed, coverage, slack)
        recommended_pct = {"low": 10.0, "medium": 15.0, "high": 20.0}[risk_level]
        suggested = round(predicted_cost * recommended_pct / 100, 2)

        return {
            "risk_level": risk_level,
            "risk_label": RISK_LABELS.get(risk_level, risk_level.title()),
            "confidence": round(confidence, 4),
            "reasons": reasons,
            "suggested_contingency": suggested,
            "recommended_contingency_pct": recommended_pct,
            "saving_tips": self._build_saving_tips(risk_level),
            "assumptions": [
                "Risk is assessed against the model's cost estimate, which carries its own error margin.",
                f"Contingency is currently set at {contingency_pct:.0f}% of the estimated cost.",
                "Labels come from a documented budget-vs-estimate rule, not from annotated real-world overruns.",
                f"A coverage ratio of {LOW_RISK_COVERAGE} counts as comfortable headroom and "
                f"{MEDIUM_RISK_COVERAGE} as the lower edge of a workable budget.",
            ],
            "method_note": RISK_LABEL_NOTE,
        }

    @staticmethod
    def _build_reasons(
        risk_level: str,
        budget: float,
        predicted_cost: float,
        committed: float,
        coverage: float,
        slack: float,
    ) -> list[str]:
        reasons: list[str] = []
        if risk_level == RISK_HIGH:
            reasons.append(
                f"Your budget of INR {budget:,.0f} is short of the INR {committed:,.0f} "
                "needed (estimate plus contingency)."
            )
            reasons.append(
                f"That is a coverage ratio of {coverage:.2f}x — you would need roughly "
                f"INR {abs(slack):,.0f} more to cover the estimate and buffer."
            )
        elif risk_level == RISK_MEDIUM:
            reasons.append(
                f"Your budget covers the estimate plus contingency {coverage:.2f}x — "
                "enough, but with very little room for price movement."
            )
            reasons.append(
                "Anything beyond the current assumptions (extra guests, overtime, "
                "last-minute vendor changes) would push this over."
            )
        else:
            reasons.append(
                f"Your budget covers the estimate plus contingency {coverage:.2f}x, "
                f"leaving about INR {slack:,.0f} of headroom."
            )
            reasons.append(
                "This plan is comfortably funded, so you can absorb moderate price "
                "movement without cutting scope."
            )
        return reasons

    @staticmethod
    def _build_saving_tips(risk_level: str) -> list[str]:
        if risk_level == RISK_HIGH:
            return [
                "Reduce guest count — catering is usually the largest single cost line.",
                "Move the catering tier down one level before cutting decoration.",
                "Choose an off-peak date or a weekday to unlock lower venue rates.",
                "Shorten the event by one hour to reduce venue and staffing time charges.",
                "Replace premium photography with a smaller package plus a rented camera.",
                "Negotiate a barebones venue and bring in your own decor and catering.",
            ]
        if risk_level == RISK_MEDIUM:
            return [
                "Trim one service tier (usually photography or decoration) to build a buffer.",
                "Ask vendors for a multi-service bundle discount.",
                "Set a firm cap on the number of vendors that need a deposit.",
                "Keep a 10-15% contingency untouched for last-minute costs.",
            ]
        return [
            "Keep the current contingency untouched rather than reallocating it.",
            "Use any remaining headroom for one memorable element (photography or a cake).",
            "Re-confirm vendor quotes closer to the date — current headroom may not hold.",
        ]


model_store = ModelStore()

