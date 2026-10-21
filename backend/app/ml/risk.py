"""Model C — Budget Risk Classification.

A ``DecisionTreeClassifier`` that labels a proposed budget as **low**, **medium**
or **high** risk of running over budget.

Label definition (documented rules, applied to the training rows)::

    total_committed = predicted_cost * (1 + contingency_pct / 100)
    coverage_ratio  = budget / total_committed

    coverage_ratio >= 1.25  -> low     (healthy headroom)
    1.00 <= coverage < 1.25 -> medium  (tight, small buffer)
    coverage < 1.00         -> high    (budget cannot cover the estimate)

These labels are *rule-derived, not human-annotated*. The tree learns to
approximate these rules from the features, which means it is a transparent
enforcement of a stated policy rather than a discovery of patterns in labelled
real-world outcomes. The API response always states this assumption.

Assumptions & limitations:
  * Predicted cost already carries the model's own error; the tree cannot see
    that error, so a "low risk" label means "low risk *given the model's
    estimate*".
  * Contingency defaults to 10% if the user does not state one.
  * Guest count enters as a scale/context signal; small events are treated as
    less risky because overruns tend to be a larger fraction of a small budget.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from app.schemas.vocabulary import RISK_HIGH, RISK_LOW, RISK_MEDIUM

RISK_FEATURE_COLUMNS = [
    "budget",
    "predicted_cost",
    "contingency_pct",
    "guest_count",
    "coverage_ratio",
    "slack_amount",
    "guest_cost_ratio",
]

RISK_LABEL_NOTE = (
    "Labels are derived from a documented rule (budget vs predicted cost plus "
    "contingency), not from human-annotated real-world overruns. The tree "
    "approximates that rule; it does not discover independent market risk."
)

# Thresholds used both to label training rows and to explain predictions.
LOW_RISK_COVERAGE = 1.25
MEDIUM_RISK_COVERAGE = 1.00


def label_risk(budget: float, predicted_cost: float, contingency_pct: float) -> str:
    """Apply the documented labelling rule."""
    if predicted_cost <= 0:
        return RISK_LOW
    committed = predicted_cost * (1 + contingency_pct / 100)
    coverage = budget / committed
    if coverage >= LOW_RISK_COVERAGE:
        return RISK_LOW
    if coverage >= MEDIUM_RISK_COVERAGE:
        return RISK_MEDIUM
    return RISK_HIGH


def risk_features(
    budget: float, predicted_cost: float, contingency_pct: float, guest_count: int
) -> dict[str, float]:
    committed = predicted_cost * (1 + contingency_pct / 100)
    coverage = (budget / committed) if committed > 0 else 1.0
    guest_cost_ratio = (predicted_cost / guest_count) if guest_count > 0 else 0.0
    return {
        "budget": float(budget),
        "predicted_cost": float(predicted_cost),
        "contingency_pct": float(contingency_pct),
        "guest_count": float(guest_count),
        "coverage_ratio": float(coverage),
        "slack_amount": float(budget - committed),
        "guest_cost_ratio": float(guest_cost_ratio),
    }



def build_risk_dataset(n_rows: int = 6000, seed: int = 7) -> pd.DataFrame:
    """Build a labelled risk dataset by sampling budgets around an estimate.

    For each row we sample a plausible estimated cost, a contingency allowance
    and a budget that is *deliberately* distributed across healthy, tight and
    under-funded cases so all three classes are represented.
    """
    rng = np.random.default_rng(seed)

    rows: list[dict[str, float | int | str]] = []
    for _ in range(n_rows):
        guests = int(np.clip(rng.lognormal(mean=4.6, sigma=0.8), 10, 1200))
        predicted_cost = float(
            np.clip(rng.lognormal(mean=11.6, sigma=1.1), 25_000, 12_000_000)
        )
        contingency_pct = float(rng.choice([0, 5, 10, 15, 20], p=[0.25, 0.25, 0.25, 0.15, 0.10]))

        committed = predicted_cost * (1 + contingency_pct / 100)
        # Budget factor spread around the committed amount produces the
        # low / medium / high mix.
        factor = float(
            rng.choice(
                [rng.uniform(1.35, 2.6), rng.uniform(1.02, 1.34), rng.uniform(0.55, 0.99)],
                p=[0.38, 0.32, 0.30],
            )
        )
        budget = committed * factor

        feats = risk_features(budget, predicted_cost, contingency_pct, guests)
        label = label_risk(budget, predicted_cost, contingency_pct)
        rows.append({**feats, "risk_label": label})

    return pd.DataFrame(rows)


def train_risk_model(
    n_rows: int = 6000, seed: int = 7
) -> tuple[DecisionTreeClassifier, dict[str, object]]:
    df = build_risk_dataset(n_rows=n_rows, seed=seed)
    X = df[RISK_FEATURE_COLUMNS]
    y = df["risk_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )

    clf = DecisionTreeClassifier(
        max_depth=8,
        min_samples_leaf=20,
        criterion="gini",
        random_state=seed,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(
        y_test, y_pred, labels=[RISK_LOW, RISK_MEDIUM, RISK_HIGH]
    ).tolist()

    importances = dict(
        zip(
            RISK_FEATURE_COLUMNS,
            [round(float(v), 6) for v in clf.feature_importances_],
        )
    )
    importances = dict(sorted(importances.items(), key=lambda kv: kv[1], reverse=True))

    metrics: dict[str, object] = {
        "model": "DecisionTreeClassifier",
        "n_samples": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "accuracy": accuracy,
        "accuracy_note": (
            "Accuracy is expected to be very high (often 1.0) because the target "
            "label is a deterministic function of the input features "
            "(coverage_ratio). The tree is therefore learning the documented "
            "labelling rule, NOT discovering independent real-world risk "
            "patterns. Treat this metric as 'the rule is faithfully reproduced', "
            "not as evidence of predictive power on unseen market data."
        ),
        "class_distribution": y.value_counts().to_dict(),
        "classification_report": report,
        "confusion_matrix": cm,
        "labels": [RISK_LOW, RISK_MEDIUM, RISK_HIGH],
        "feature_importances": importances,
        "max_depth": clf.max_depth,
        "min_samples_leaf": clf.min_samples_leaf,
        "label_note": RISK_LABEL_NOTE,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    return clf, metrics
