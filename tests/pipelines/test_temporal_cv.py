"""Unit tests for Brasaland temporal split and TimeSeriesSplit chronology."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import TimeSeriesSplit

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from sales_forecast.data import (  # noqa: E402
    MONTH_COL,
    assert_chronological,
    build_feature_matrix,
    load_consolidated_sales,
    temporal_train_test_split,
)


def test_temporal_train_test_split_is_chronological():
    raw = load_consolidated_sales()
    featured = build_feature_matrix(raw)
    series_start = raw[MONTH_COL].min()
    train, test = temporal_train_test_split(
        featured, train_years=8, test_years=2, series_start=series_start
    )

    assert_chronological(train[MONTH_COL].to_numpy())
    assert_chronological(test[MONTH_COL].to_numpy())
    assert train[MONTH_COL].max() < test[MONTH_COL].min()
    # CONTEXT: train ends before 2024-01, test covers 2024-2025
    assert train[MONTH_COL].max() < pd.Timestamp("2024-01-01")
    assert test[MONTH_COL].min() >= pd.Timestamp("2024-01-01")
    assert test[MONTH_COL].max() <= pd.Timestamp("2025-12-01")


def test_time_series_split_preserves_order_and_no_future_leak():
    n_samples = 96  # 8 years of monthly train window
    tscv = TimeSeriesSplit(n_splits=5)
    for train_idx, test_idx in tscv.split(np.arange(n_samples)):
        assert_chronological(train_idx)
        assert_chronological(test_idx)
        assert train_idx.max() < test_idx.min()
        assert set(train_idx).isdisjoint(set(test_idx))


def test_assert_chronological_rejects_shuffle():
    with pytest.raises(AssertionError):
        assert_chronological(np.array([0, 2, 1, 3]))
