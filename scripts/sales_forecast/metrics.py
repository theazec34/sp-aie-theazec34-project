"""Regression metrics: MAE/RMSE plus CONTEXT MSE, PSI, Gini, K2."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def mape_pct(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100.0)


def gini_normalized(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Normalized Gini on predicted ranking of monthly revenue."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    n = len(y_true)
    if n < 2 or np.allclose(y_true, y_true[0]):
        return 0.0
    order = np.argsort(y_pred)
    y_sorted = y_true[order]
    cum = np.cumsum(y_sorted)
    gini = (cum.sum() / cum[-1] - (n + 1) / 2.0) / n
    perfect = np.sort(y_true)
    cum_p = np.cumsum(perfect)
    gini_p = (cum_p.sum() / cum_p[-1] - (n + 1) / 2.0) / n
    if abs(gini_p) < 1e-12:
        return 0.0
    return float(gini / gini_p)


def population_stability_index(
    expected: np.ndarray,
    actual: np.ndarray,
    *,
    buckets: int = 10,
) -> float:
    """PSI between train (expected) and test (actual) target distributions."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    breaks = np.unique(np.quantile(expected, np.linspace(0, 1, buckets + 1)))
    if len(breaks) < 3:
        return 0.0
    exp_counts = np.histogram(expected, bins=breaks)[0].astype(float)
    act_counts = np.histogram(actual, bins=breaks)[0].astype(float)
    exp_pct = np.clip(exp_counts / exp_counts.sum(), 1e-4, None)
    act_pct = np.clip(act_counts / act_counts.sum(), 1e-4, None)
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def k2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """CONTEXT K2 Score ≡ R²."""
    return float(r2_score(y_true, y_pred))


def regression_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    train_target: np.ndarray | None = None,
) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mse = float(mean_squared_error(y_true, y_pred))
    report = {
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mape_pct": mape_pct(y_true, y_pred),
        "gini": gini_normalized(y_true, y_pred),
        "k2": k2_score(y_true, y_pred),
    }
    if train_target is not None:
        report["psi"] = population_stability_index(train_target, y_true)
    return report
