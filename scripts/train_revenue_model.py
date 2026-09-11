#!/usr/bin/env python3
"""Train Brasaland revenue regressor (8y train / 2y test) and pick best model."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from sales_forecast.data import (  # noqa: E402
    FEATURE_COLS,
    MONTH_COL,
    TARGET_COL,
    build_feature_matrix,
    load_consolidated_sales,
    temporal_train_test_split,
)
from sales_forecast.metrics import regression_report  # noqa: E402

MODEL_DIR = REPO / "models"
EVAL_DIR = REPO / "data" / "eval"


def candidate_models(seed: int = 42) -> dict:
    return {
        "random_forest": RandomForestRegressor(
            n_estimators=300,
            max_depth=5,
            min_samples_leaf=4,
            max_features="sqrt",
            random_state=seed,
            n_jobs=-1,
        ),
        "xgboost": XGBRegressor(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=5.0,
            min_child_weight=3,
            objective="reg:squarederror",
            random_state=seed,
            n_jobs=-1,
        ),
    }


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_consolidated_sales()
    featured = build_feature_matrix(raw)
    train, test = temporal_train_test_split(
        featured,
        train_years=8,
        test_years=2,
        series_start=raw[MONTH_COL].min(),
    )

    x_train = train[FEATURE_COLS]
    y_train = train[TARGET_COL].to_numpy()
    x_test = test[FEATURE_COLS]
    y_test = test[TARGET_COL].to_numpy()

    results: dict = {}
    best_name = None
    best_rmse = float("inf")
    best_model = None

    for name, model in candidate_models().items():
        model.fit(x_train, y_train)
        pred_test = model.predict(x_test)
        pred_train = model.predict(x_train)
        report = regression_report(y_test, pred_test, train_target=y_train)
        report["train_rmse"] = float(np.sqrt(np.mean((y_train - pred_train) ** 2)))
        report["train_mae"] = float(np.mean(np.abs(y_train - pred_train)))
        results[name] = report
        print(
            f"[{name}] test RMSE={report['rmse']:.2f} MAE={report['mae']:.2f} "
            f"MAPE={report['mape_pct']:.2f}% Gini={report['gini']:.3f} "
            f"K2={report['k2']:.3f} PSI={report['psi']:.3f}"
        )
        if report["rmse"] < best_rmse:
            best_rmse = report["rmse"]
            best_name = name
            best_model = model

    assert best_model is not None and best_name is not None
    artifact = {
        "model_name": best_name,
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "train_months": [
            str(train[MONTH_COL].min().date()),
            str(train[MONTH_COL].max().date()),
        ],
        "test_months": [
            str(test[MONTH_COL].min().date()),
            str(test[MONTH_COL].max().date()),
        ],
        "metrics": results,
        "selection_rule": "lowest test RMSE (ops cost of large misses)",
    }
    model_path = MODEL_DIR / "revenue_regressor.joblib"
    joblib.dump({"model": best_model, "meta": artifact}, model_path)
    (EVAL_DIR / "train_metrics.json").write_text(
        json.dumps(artifact, indent=2), encoding="utf-8"
    )
    print(f"Selected {best_name} → {model_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
