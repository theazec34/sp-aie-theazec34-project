"""Load Brasaland sales and build time-safe features (CONTEXT field names)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_SALES_PATH = REPO_ROOT / "data" / "raw" / "brasaland_sales.csv"

MONTH_COL = "month"
TARGET_COL = "revenue_usd"
COVERS_COL = "covers_served"
TICKET_COL = "avg_ticket_usd"
MARKET_COL = "market"
MARKET_CONSOLIDATED = "consolidated"

FEATURE_COLS = [
    "year",
    "month_num",
    "month_sin",
    "month_cos",
    "lag_1_revenue_usd",
    "lag_12_revenue_usd",
    "roll_mean_3_revenue_usd",
    "roll_mean_12_revenue_usd",
    "lag_1_covers_served",
    "lag_12_covers_served",
]


def load_consolidated_sales(path: Path | None = None) -> pd.DataFrame:
    """Load monthly consolidated rows sorted chronologically."""
    path = path or RAW_SALES_PATH
    df = pd.read_csv(path, parse_dates=[MONTH_COL])
    required = {MONTH_COL, TARGET_COL, COVERS_COL, TICKET_COL, MARKET_COL}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing CONTEXT columns in {path}: {sorted(missing)}")

    df = df.loc[df[MARKET_COL] == MARKET_CONSOLIDATED].copy()
    df = df.sort_values(MONTH_COL).reset_index(drop=True)
    if df.empty:
        raise ValueError("No consolidated market rows found")
    if (df[TARGET_COL] <= 0).any():
        raise ValueError("Business rule violated: revenue_usd must be positive")
    return df


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer lag/seasonality features without shuffling time.

    Contemporaneous covers/ticket are excluded to avoid leakage
    (revenue ≈ covers × ticket). Forecasts use lagged demand only.
    """
    out = df.copy()
    out["year"] = out[MONTH_COL].dt.year
    out["month_num"] = out[MONTH_COL].dt.month
    out["month_sin"] = np.sin(2 * np.pi * out["month_num"] / 12)
    out["month_cos"] = np.cos(2 * np.pi * out["month_num"] / 12)

    out["lag_1_revenue_usd"] = out[TARGET_COL].shift(1)
    out["lag_12_revenue_usd"] = out[TARGET_COL].shift(12)
    out["roll_mean_3_revenue_usd"] = out[TARGET_COL].shift(1).rolling(3).mean()
    out["roll_mean_12_revenue_usd"] = out[TARGET_COL].shift(1).rolling(12).mean()
    out["lag_1_covers_served"] = out[COVERS_COL].shift(1)
    out["lag_12_covers_served"] = out[COVERS_COL].shift(12)

    return out.dropna().reset_index(drop=True)


def temporal_train_test_split(
    featured: pd.DataFrame,
    *,
    train_years: int = 8,
    test_years: int = 2,
    series_start: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by CONTEXT calendar windows on the original series start.

    Brasaland CONTEXT: first 8 years train, last 2 years test on the raw
    2016-01→2025-12 series. Feature lags drop early months, so the train
    block is ``[start, start+8y)`` and test is ``[start+8y, start+10y)``.
    """
    if series_start is None:
        # Infer original start as first month minus max lag used (12).
        series_start = featured[MONTH_COL].min() - pd.DateOffset(months=12)
    train_end = series_start + pd.DateOffset(years=train_years)
    test_end = train_end + pd.DateOffset(years=test_years)
    train = featured.loc[
        (featured[MONTH_COL] >= series_start) & (featured[MONTH_COL] < train_end)
    ].copy()
    test = featured.loc[
        (featured[MONTH_COL] >= train_end) & (featured[MONTH_COL] < test_end)
    ].copy()
    if train.empty or test.empty:
        raise ValueError(
            f"Empty split train={len(train)} test={len(test)} "
            f"(window {series_start.date()} → {test_end.date()})"
        )
    if train[MONTH_COL].max() >= test[MONTH_COL].min():
        raise ValueError("Train/test temporal leak: train max >= test min")
    return train, test


def assert_chronological(index_like) -> None:
    """Raise if values are not strictly increasing."""
    arr = np.asarray(index_like)
    if arr.size < 2:
        return
    if not np.all(arr[1:] > arr[:-1]):
        raise AssertionError("Sequence is not strictly chronological")
