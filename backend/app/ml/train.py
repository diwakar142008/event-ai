"""Training pipeline for the three Eventora ML models.

Run with::

    python -m app.ml.train --all

Artifacts are written to ``backend/ml_artifacts/`` (override with
``ML_MODEL_DIR``). Every artifact is a full ``sklearn`` ``Pipeline`` so that
inference uses exactly the same preprocessing that was fitted during training.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from app.config import settings
from app.ml.dataset import (
    COST_CATEGORICAL_FEATURES,
    COST_FEATURE_COLUMNS,
    COST_NUMERIC_FEATURES,
    CURRENCY,
    DATASET_NOTE,
    generate_cost_dataset,
)
from app.ml.recommendation import (
    RECOMMENDATION_ITEMS,
    build_recommendation_index,
    recommend_from_index,
    recommendation_metrics,
)
from app.ml.risk import (
    RISK_FEATURE_COLUMNS,
    RISK_LABEL_NOTE,
    build_risk_dataset,
    train_risk_model,
)

COST_MODEL_FILE = "cost_model.joblib"
REC_MODEL_FILE = "recommendation_index.joblib"
RISK_MODEL_FILE = "budget_risk_model.joblib"
METRICS_FILE = "metrics.json"


@dataclass
class CostModelMetrics:
    model: str = "RandomForestRegressor"
    n_samples: int = 0
    n_train: int = 0
    n_test: int = 0
    mae: float = 0.0
    rmse: float = 0.0
    r2: float = 0.0
    mape: float = 0.0
    train_rmse: float = 0.0
    feature_importances: dict[str, float] = None  # type: ignore[assignment]
    dataset_note: str = DATASET_NOTE
    trained_at: str = ""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_cost_pipeline() -> Pipeline:
    """Preprocessing (OHE + scaling) + Random Forest regressor."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                StandardScaler(),
                COST_NUMERIC_FEATURES,
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                COST_CATEGORICAL_FEATURES,
            ),
        ]
    )
    regressor = RandomForestRegressor(
        # 160 trees with a depth cap keeps the artifact small (a few hundred KB
        # after compression) while holding accuracy close to the 300-tree
        # baseline measured during development.
        n_estimators=160,
        max_depth=18,
        min_samples_leaf=2,
        max_features="sqrt",
        n_jobs=-1,
        random_state=42,
    )
    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])


def train_cost_model(n_rows: int = 4000, seed: int = 42) -> tuple[Pipeline, CostModelMetrics]:
    df = generate_cost_dataset(n_rows=n_rows, seed=seed)
    X = df[COST_FEATURE_COLUMNS]
    y = df["total_cost"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, shuffle=True
    )

    pipeline = build_cost_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_pred_train = pipeline.predict(X_train)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))
    nonzero = y_test.to_numpy() != 0
    mape = float(
        np.mean(np.abs((y_test.to_numpy()[nonzero] - y_pred[nonzero]) / y_test.to_numpy()[nonzero]))
        * 100
    )

    # Map feature importances back to readable feature names.
    rf = pipeline.named_steps["regressor"]
    pre = pipeline.named_steps["preprocessor"]
    cat_names = list(pre.named_transformers_["cat"].get_feature_names_out(COST_CATEGORICAL_FEATURES))
    num_names = list(pre.named_transformers_["num"].get_feature_names_out(COST_NUMERIC_FEATURES))
    names = [n.replace("cat__", "").replace("num__", "") for n in cat_names + num_names]
    importances = dict(zip(names, rf.feature_importances_.tolist()))
    importances = dict(sorted(importances.items(), key=lambda kv: kv[1], reverse=True)[:12])

    metrics = CostModelMetrics(
        n_samples=int(len(df)),
        n_train=int(len(X_train)),
        n_test=int(len(X_test)),
        mae=mae,
        rmse=rmse,
        r2=r2,
        mape=mape,
        train_rmse=float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
        feature_importances=importances,
        trained_at=_utc_now_iso(),
    )
    return pipeline, metrics



def train_recommendation_model() -> tuple[Any, dict[str, Any]]:
    model, items, meta = build_recommendation_index()
    metrics = recommendation_metrics(meta)
    return {"model": model, "items": items, "meta": meta}, metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the Eventora AI models.")
    parser.add_argument("--all", action="store_true", help="Train all three models.")
    parser.add_argument("--cost", action="store_true", help="Train the cost model.")
    parser.add_argument("--recommend", action="store_true", help="Build the recommendation index.")
    parser.add_argument("--risk", action="store_true", help="Train the budget-risk model.")
    parser.add_argument("--rows", type=int, default=4000, help="Rows for the cost dataset.")
    args = parser.parse_args(argv)

    if not any([args.all, args.cost, args.recommend, args.risk]):
        parser.error("Choose at least one of --all, --cost, --recommend, --risk")

    out_dir = settings.model_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = out_dir / METRICS_FILE
    metrics: dict[str, Any] = {}
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    if args.all or args.cost:
        print("[1/3] Training cost model (RandomForestRegressor)...")
        pipeline, cost_metrics = train_cost_model(n_rows=args.rows)
        joblib.dump(pipeline, out_dir / COST_MODEL_FILE, compress=3)
        metrics["cost_model"] = asdict(cost_metrics)
        print(
            f"      MAE={cost_metrics.mae:,.0f}  RMSE={cost_metrics.rmse:,.0f}  "
            f"R2={cost_metrics.r2:.4f}  MAPE={cost_metrics.mape:.2f}%"
        )

    if args.all or args.recommend:
        print("[2/3] Building recommendation index (NearestNeighbors)...")
        payload, rec_metrics = train_recommendation_model()
        joblib.dump(payload, out_dir / REC_MODEL_FILE, compress=3)
        metrics["recommendation_model"] = rec_metrics
        print(f"      {rec_metrics['n_items']} catalogue items indexed")

    if args.all or args.risk:
        print("[3/3] Training budget risk classifier (DecisionTreeClassifier)...")
        clf, risk_metrics = train_risk_model()
        joblib.dump(clf, out_dir / RISK_MODEL_FILE, compress=3)
        metrics["risk_model"] = risk_metrics
        print(f"      accuracy={risk_metrics['accuracy']:.4f}")

    metrics["generated_at"] = _utc_now_iso()
    metrics["dataset_note"] = DATASET_NOTE
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")

    print(f"\nArtifacts written to {out_dir}")
    print(f"Metrics written to {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
