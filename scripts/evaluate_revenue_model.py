#!/usr/bin/env python3
"""Technical evaluation for staging: TimeSeriesSplit + learning curve + report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.base import clone
from sklearn.model_selection import TimeSeriesSplit, learning_curve

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from sales_forecast.data import (  # noqa: E402
    FEATURE_COLS,
    MONTH_COL,
    TARGET_COL,
    assert_chronological,
    build_feature_matrix,
    load_consolidated_sales,
    temporal_train_test_split,
)
from sales_forecast.metrics import regression_report  # noqa: E402
from train_revenue_model import candidate_models  # noqa: E402

MODEL_PATH = REPO / "models" / "brasaland_sales_forecast.joblib"
LEGACY_MODEL_PATH = REPO / "models" / "revenue_regressor.joblib"
EVAL_DIR = REPO / "data" / "eval"
N_SPLITS = 5


def verify_time_series_splits(n_samples: int, n_splits: int = N_SPLITS) -> list[dict]:
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_info = []
    for fold, (train_idx, test_idx) in enumerate(tscv.split(np.arange(n_samples)), start=1):
        assert_chronological(train_idx)
        assert_chronological(test_idx)
        if train_idx.max() >= test_idx.min():
            raise AssertionError(
                f"Fold {fold} leaks future: train_max={train_idx.max()} "
                f">= test_min={test_idx.min()}"
            )
        fold_info.append(
            {
                "fold": fold,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "train_idx_max": int(train_idx.max()),
                "test_idx_min": int(test_idx.min()),
            }
        )
    return fold_info


def cross_validate_model(model, x, y, n_splits: int = N_SPLITS) -> dict:
    tscv = TimeSeriesSplit(n_splits=n_splits)
    mae_scores: list[float] = []
    rmse_scores: list[float] = []
    for train_idx, test_idx in tscv.split(x):
        assert train_idx.max() < test_idx.min()
        m = clone(model)
        m.fit(x.iloc[train_idx], y[train_idx])
        pred = m.predict(x.iloc[test_idx])
        report = regression_report(y[test_idx], pred)
        mae_scores.append(report["mae"])
        rmse_scores.append(report["rmse"])
    return {
        "n_splits": n_splits,
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores, ddof=1)),
        "rmse_mean": float(np.mean(rmse_scores)),
        "rmse_std": float(np.std(rmse_scores, ddof=1)),
        "mae_folds": mae_scores,
        "rmse_folds": rmse_scores,
    }


def plot_learning_curve_fig(model, x, y, out_path: Path) -> dict:
    train_sizes, train_scores, val_scores = learning_curve(
        clone(model),
        x,
        y,
        cv=TimeSeriesSplit(n_splits=N_SPLITS),
        scoring="neg_root_mean_squared_error",
        train_sizes=np.linspace(0.3, 1.0, 6),
        shuffle=False,
        n_jobs=-1,
    )
    train_rmse = -train_scores.mean(axis=1)
    val_rmse = -val_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    val_std = val_scores.std(axis=1)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(train_sizes, train_rmse, "o-", color="#1B4F72", label="Train RMSE")
    ax.fill_between(
        train_sizes,
        train_rmse - train_std,
        train_rmse + train_std,
        alpha=0.15,
        color="#1B4F72",
    )
    ax.plot(train_sizes, val_rmse, "o-", color="#C0392B", label="Validation RMSE")
    ax.fill_between(
        train_sizes,
        val_rmse - val_std,
        val_rmse + val_std,
        alpha=0.15,
        color="#C0392B",
    )
    ax.set_xlabel("Training months (chronological)")
    ax.set_ylabel("RMSE (USD)")
    ax.set_title("Brasaland revenue model — learning curve (TimeSeriesSplit)")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)

    return {
        "train_sizes": train_sizes.tolist(),
        "train_rmse": train_rmse.tolist(),
        "val_rmse": val_rmse.tolist(),
        "final_train_rmse": float(train_rmse[-1]),
        "final_val_rmse": float(val_rmse[-1]),
        "final_gap": float(val_rmse[-1] - train_rmse[-1]),
    }


def plot_prediction_vs_actual(months, y_true, y_pred, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(months, y_true, "o-", color="#1B4F72", label="Actual revenue_usd")
    ax.plot(months, y_pred, "s--", color="#C0392B", label="Predicted revenue_usd")
    residual = np.asarray(y_true) - np.asarray(y_pred)
    band = float(np.std(residual))
    ax.fill_between(
        months,
        np.asarray(y_pred) - band,
        np.asarray(y_pred) + band,
        color="#C0392B",
        alpha=0.15,
        label="±1σ residual band",
    )
    ax.set_title("Brasaland hold-out: prediction vs actual (last 2 years)")
    ax.set_ylabel("revenue_usd")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def diagnose(curve: dict, cv: dict) -> tuple[str, str]:
    final_train = curve["final_train_rmse"]
    final_val = curve["final_val_rmse"]
    gap = curve["final_gap"]
    rel_gap = gap / max(final_val, 1.0)
    cv_rel_std = cv["rmse_std"] / max(cv["rmse_mean"], 1.0)

    if final_train > 80_000 and final_val > 80_000 and rel_gap < 0.15:
        return (
            "underfitting",
            "Train and validation RMSE both stay high and close: the model fails to "
            "capture Brasaland seasonality (Jan trough / Dec peak). Concrete action: "
            "increase XGBoost capacity carefully (max_depth 5–6) and add an explicit "
            "lag_12 × month interaction; do NOT only append more undifferentiated rows.",
        )
    if rel_gap > 0.25 and final_train < final_val * 0.75:
        return (
            "overfitting",
            "Persistent train≪validation gap: model memorizes monthly noise. "
            "Concrete action: raise XGBoost regularization (reg_lambda=2–5, "
            "min_child_weight=3, max_depth≤3) and use early stopping on the last "
            "temporal fold; do not grow n_estimators without that control.",
        )
    return (
        "bien_ajustado",
        "Curves are close with acceptable validation error and stable CV "
        f"(RMSE {cv['rmse_mean']:.0f}±{cv['rmse_std']:.0f}). Concrete action before "
        "staging: freeze current hyperparameters, monitor monthly PSI after new "
        "location openings, and alert if out-of-fold RMSE rises more than "
        f"{max(cv_rel_std * 100, 10):.0f}% above the CV mean.",
    )


def write_report(
    *,
    model_name: str,
    holdout: dict,
    cv: dict,
    curve: dict,
    diagnosis: str,
    action: str,
    fold_guard: list[dict],
    path: Path,
) -> None:
    lines = [
        "# Evaluation report — Brasaland revenue regressor",
        "",
        "## Business context (Brasaland)",
        "",
        "- **Mariana (CEO):** needs to separate good vs bad months (Gini) and an error "
        "she can read as a percentage (MAPE) before funding a full executive dashboard.",
        "- **Felipe (Operations):** anticipates ingredient purchases; **underestimating** "
        "sales causes stockouts and emergency buys (asymmetric high cost).",
        "- **Lucía (Procurement):** projects volume to negotiate beef prices; large misses "
        "in peak season (December) distort coverage.",
        "",
        "### Primary metric: RMSE (not MAE)",
        "",
        "For Brasaland the cost is non-linear: missing December or an event month hurts "
        "more than many small misses. **RMSE** penalizes those large misses and better "
        "matches Felipe/Lucía operational risk. **MAE** is reported for communication "
        "(average USD deviation) but **staging decisions use RMSE**.",
        "",
        f"## Model under evaluation: `{model_name}`",
        "",
        "CONTEXT temporal split: **8 years train / 2 years test** (no shuffle).",
        "",
        "## Hold-out test (last 2 years)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| MAE | ${holdout['mae']:,.2f} |",
        f"| RMSE | ${holdout['rmse']:,.2f} |",
        f"| MSE | {holdout['mse']:,.2f} USD² |",
        f"| MAPE | {holdout['mape_pct']:.2f}% |",
        f"| Gini | {holdout['gini']:.3f} |",
        f"| K2 (R²) | {holdout['k2']:.3f} |",
        f"| PSI (train→test target) | {holdout['psi']:.3f} |",
        "",
        f"## Temporal cross-validation (`TimeSeriesSplit`, {cv['n_splits']} folds)",
        "",
        "Verified: no fold mixes future into the past "
        f"(guards: `{fold_guard}`).",
        "",
        f"- **MAE:** {cv['mae_mean']:,.2f} ± {cv['mae_std']:,.2f} USD",
        f"- **RMSE:** {cv['rmse_mean']:,.2f} ± {cv['rmse_std']:,.2f} USD",
        "",
        "## Learning curve",
        "",
        "File: `data/eval/learning_curve.png`",
        "",
        f"- Final train RMSE: ${curve['final_train_rmse']:,.2f}",
        f"- Final validation RMSE: ${curve['final_val_rmse']:,.2f}",
        f"- Gap (val − train): ${curve['final_gap']:,.2f}",
        "",
        "## Diagnosis",
        "",
        f"**Classification: `{diagnosis}`**",
        "",
        action,
        "",
        "## Staging recommendation",
        "",
        "Promote to staging **only if** CV RMSE mean±std stays bounded and train→test "
        f"PSI remains < 0.25. Current PSI = {holdout['psi']:.3f}.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_PATH if MODEL_PATH.exists() else LEGACY_MODEL_PATH
    if not model_path.exists():
        raise SystemExit(
            "Missing trained model. Run: uv run python scripts/train_sales_forecast.py"
        )

    bundle = joblib.load(model_path)
    model = bundle["model"]
    meta = bundle["meta"]
    model_name = meta["model_name"]

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

    pred_test = model.predict(x_test)
    holdout = regression_report(y_test, pred_test, train_target=y_train)
    plot_prediction_vs_actual(
        test[MONTH_COL], y_test, pred_test,
        EVAL_DIR / "prediction_vs_actual.png",
    )

    fold_guard = verify_time_series_splits(len(x_train), N_SPLITS)
    template = candidate_models()[model_name]
    cv = cross_validate_model(template, x_train, y_train, N_SPLITS)
    curve = plot_learning_curve_fig(
        template, x_train, y_train, EVAL_DIR / "learning_curve.png"
    )
    diagnosis, action = diagnose(curve, cv)
    write_report(
        model_name=model_name,
        holdout=holdout,
        cv=cv,
        curve=curve,
        diagnosis=diagnosis,
        action=action,
        fold_guard=fold_guard,
        path=EVAL_DIR / "evaluation_report.md",
    )

    summary = {
        "model_name": model_name,
        "diagnosis": diagnosis,
        "holdout": holdout,
        "cv": cv,
        "learning_curve": curve,
        "time_series_fold_guards": fold_guard,
        "test_window": [
            str(test[MONTH_COL].min().date()),
            str(test[MONTH_COL].max().date()),
        ],
    }
    (EVAL_DIR / "evaluation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "diagnosis": diagnosis,
                "cv_rmse": cv["rmse_mean"],
                "holdout_rmse": holdout["rmse"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
