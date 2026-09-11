#!/usr/bin/env python3
"""Brasaland sales forecast — train RF/XGBoost (8y/2y), report MSE/PSI/Gini/K2, plot band.

Algorithm choice (documented for stakeholders)
---------------------------------------------
We train **both** Random Forest and XGBoost with ``random_state=42`` and keep the
model with lowest test RMSE.

- **Random Forest**: easier to explain to Mariana/Finance (bagging + feature
  importance); fewer knobs.
- **XGBoost**: usually better precision on seasonal series; harder to explain.

For Brasaland, Felipe (Ops) and Lucía (Procurement) need accurate monthly
``revenue_usd`` to buy ingredients and hedge beef. Precision wins over
storytelling for the production artifact, so **XGBoost is preferred when its
test RMSE is better**; RF remains the fallback if gaps are tiny and Finance
demands interpretability.

Finance-facing error: we always print **MAE (USD)** and **MAPE (%)** alongside
MSE — MAE is the "average dollars off" number Finance understands; MSE alone
is not enough (CONTEXT).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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

RANDOM_STATE = 42
MODEL_DIR = REPO / "models"
FORECAST_DIR = REPO / "data" / "forecast"

# Why each metric (CONTEXT + Finance)
METRIC_NOTES = {
    "mse": "Mean squared error in USD² — penalizes large misses; translate via RMSE/MAPE for Felipe/Mariana.",
    "psi": "Population Stability Index train→test — high PSI ⇒ structural shift (growth/new sites); retrain.",
    "gini": "Ranking quality of good vs bad months — low Gini ⇒ Mariana cannot spot weak months early.",
    "k2": "K2 Score ≡ R² — share of revenue variance explained on the test window.",
}


def candidate_models(seed: int = RANDOM_STATE) -> dict:
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


def prediction_band(model, x, y_train_resid_std: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Point forecast plus ±1σ residual band (variability range for stakeholders)."""
    pred = np.asarray(model.predict(x), dtype=float)
    low = pred - y_train_resid_std
    high = pred + y_train_resid_std
    return pred, low, high


def plot_forecast_with_band(months, y_true, y_pred, y_low, y_high, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(months, y_true, "o-", color="#1B4F72", label="Actual revenue_usd")
    ax.plot(months, y_pred, "s--", color="#C0392B", label="Predicted revenue_usd")
    ax.fill_between(
        months,
        y_low,
        y_high,
        color="#C0392B",
        alpha=0.2,
        label="Variability band (±1σ train residual)",
    )
    ax.set_title("Brasaland sales forecast — test years (prediction + variability)")
    ax.set_ylabel("revenue_usd")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def write_forecast_report(artifact: dict, path: Path) -> None:
    best = artifact["model_name"]
    m = artifact["metrics"][best]
    lines = [
        "# Brasaland sales forecast — training report",
        "",
        "## Algorithm choice",
        "",
        artifact["algorithm_justification"],
        "",
        f"**Selected model:** `{best}` (random_state={RANDOM_STATE})",
        "",
        "## Train / test split (CONTEXT)",
        "",
        f"- Train months: {artifact['train_months'][0]} → {artifact['train_months'][1]}",
        f"- Test months: {artifact['test_months'][0]} → {artifact['test_months'][1]}",
        "- Rule: first **8 years** train, last **2 years** test; no shuffle / no leakage.",
        "",
        "## Test-set metrics (required)",
        "",
        "| Metric | Value | Meaning |",
        "|---|---|---|",
        f"| MSE | {m['mse']:,.2f} USD² | {METRIC_NOTES['mse']} |",
        f"| RMSE | ${m['rmse']:,.2f} | Square-root of MSE (same units as sales). |",
        f"| MAE | ${m['mae']:,.2f} | Finance-friendly average dollar error. |",
        f"| MAPE | {m['mape_pct']:.2f}% | Percent error Felipe/Mariana can read. |",
        f"| PSI | {m['psi']:.3f} | {METRIC_NOTES['psi']} |",
        f"| Gini | {m['gini']:.3f} | {METRIC_NOTES['gini']} |",
        f"| K2 Score | {m['k2']:.3f} | {METRIC_NOTES['k2']} |",
        "",
        "### Why low MSE is not enough",
        "",
        "A low MSE can hide ranking failures (Gini) or a train/test distribution shift "
        "(PSI). Brasaland needs both accurate dollars **and** early warning on weak "
        "months; CONTEXT asks for all four metrics on the **test** set.",
        "",
        "## Visualization",
        "",
        "See `data/forecast/prediction_band.png` — actual vs prediction with variability band "
        "for the 2 test years.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    FORECAST_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_consolidated_sales()
    # Basic cleaning: CONTEXT already has no nulls; drop any accidental empties.
    raw = raw.dropna(subset=[TARGET_COL, MONTH_COL]).copy()
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
        report = regression_report(y_test, pred_test, train_target=y_train)
        results[name] = report
        print(
            f"[{name}] MSE={report['mse']:.2f} PSI={report['psi']:.3f} "
            f"Gini={report['gini']:.3f} K2={report['k2']:.3f} "
            f"| MAE=${report['mae']:.2f} MAPE={report['mape_pct']:.2f}%"
        )
        if report["rmse"] < best_rmse:
            best_rmse = report["rmse"]
            best_name = name
            best_model = model

    assert best_model is not None and best_name is not None

    # Variability from train residuals of the selected model
    train_resid_std = float(np.std(y_train - best_model.predict(x_train)))
    pred, low, high = prediction_band(best_model, x_test, train_resid_std)
    plot_forecast_with_band(
        test[MONTH_COL],
        y_test,
        pred,
        low,
        high,
        FORECAST_DIR / "prediction_band.png",
    )

    justification = (
        "Compared Random Forest (explainability for Mariana/Finance) vs XGBoost "
        "(precision for Felipe/Lucía purchasing). Selected by lowest test RMSE with "
        f"fixed random_state={RANDOM_STATE}. Winner: **{best_name}**."
    )
    artifact = {
        "model_name": best_name,
        "random_state": RANDOM_STATE,
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
        "selection_rule": "lowest test RMSE",
        "algorithm_justification": justification,
        "metric_notes": METRIC_NOTES,
        "train_residual_std": train_resid_std,
    }

    model_path = MODEL_DIR / "brasaland_sales_forecast.joblib"
    # Keep legacy name used by the evaluation milestone
    legacy_path = MODEL_DIR / "revenue_regressor.joblib"
    payload = {"model": best_model, "meta": artifact}
    joblib.dump(payload, model_path)
    joblib.dump(payload, legacy_path)

    (FORECAST_DIR / "metrics.json").write_text(
        json.dumps(artifact, indent=2), encoding="utf-8"
    )
    write_forecast_report(artifact, FORECAST_DIR / "forecast_report.md")
    print(f"Selected {best_name} → {model_path}")
    print(f"Report → {FORECAST_DIR / 'forecast_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
