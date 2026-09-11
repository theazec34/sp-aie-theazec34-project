"""Unit tests for Brasaland 8y/2y sales-forecast split (no leakage)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from sales_forecast.data import (  # noqa: E402
    MONTH_COL,
    TARGET_COL,
    assert_chronological,
    build_feature_matrix,
    load_consolidated_sales,
    temporal_train_test_split,
)


def test_eight_two_year_split_has_no_leakage():
    """CONTEXT rule: first 8 years train, last 2 years test; no overlap."""
    raw = load_consolidated_sales()
    assert raw[TARGET_COL].notna().all()
    featured = build_feature_matrix(raw)
    train, test = temporal_train_test_split(
        featured,
        train_years=8,
        test_years=2,
        series_start=raw[MONTH_COL].min(),
    )

    assert_chronological(train[MONTH_COL].to_numpy())
    assert_chronological(test[MONTH_COL].to_numpy())
    assert train[MONTH_COL].max() < test[MONTH_COL].min()
    assert set(train[MONTH_COL]).isdisjoint(set(test[MONTH_COL]))

    # Calendar windows on original series 2016→2025
    assert train[MONTH_COL].max() < pd.Timestamp("2024-01-01")
    assert test[MONTH_COL].min() >= pd.Timestamp("2024-01-01")
    assert test[MONTH_COL].max() <= pd.Timestamp("2025-12-01")
    assert test["year"].nunique() == 2


def test_context_columns_present():
    raw = load_consolidated_sales()
    for col in ("month", "revenue_usd", "covers_served", "avg_ticket_usd", "market"):
        assert col in raw.columns
