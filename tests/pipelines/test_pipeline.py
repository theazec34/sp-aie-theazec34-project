"""Unit tests for weekly cost & waste KPI transforms (no DB / no network).

Run from monorepo root:

    python -m pytest tests/pipelines/test_pipeline.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.process.weekly_kpis import (
    compute_price_alert_events_by_location,
    compute_purchase_cost_by_location,
    compute_stockout_events_by_location,
    compute_waste_cost_by_location,
    compute_waste_ratio,
    line_cost_from_tags,
    refine_and_aggregate,
)


def _events_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


@pytest.fixture()
def sample_telemetry_rows() -> list[dict]:
    """In-memory telemetry shaped like telemetry_events rows (CONTEXT vocabulary)."""
    return [
        {
            "event_id": "a1",
            "event_type": "inbound_order_created",
            "timestamp": "2026-08-24T12:00:00Z",
            "tags": {
                "location_id": 1,
                "country": "CO",
                "quantity": 10,
                "unit_cost": 1000,
                "total_cost": 10000,
                "currency": "COP",
            },
        },
        {
            "event_id": "a2",
            "event_type": "stock_waste_registered",
            "timestamp": "2026-08-24T13:00:00Z",
            "tags": {
                "location_id": 1,
                "country": "CO",
                "quantity": 1,
                "unit_cost": 1000,
                "total_cost": 1000,
                "reason": "expired",
                "currency": "COP",
            },
        },
        {
            "event_id": "a3",
            "event_type": "stock_threshold_triggered",
            "timestamp": "2026-08-24T14:00:00Z",
            "tags": {"location_id": 1, "country": "CO", "threshold": 10},
        },
        {
            "event_id": "a4",
            "event_type": "ingredient_price_variance_detected",
            "timestamp": "2026-08-24T15:00:00Z",
            "tags": {
                "location_id": 1,
                "country": "CO",
                "unit_cost": 1200,
                "baseline_unit_cost": 1000,
            },
        },
        {
            "event_id": "b1",
            "event_type": "inbound_order_created",
            "timestamp": "2026-08-25T12:00:00Z",
            "tags": {
                "location_id": 2,
                "country": "US",
                "quantity": 5,
                "unit_cost": 4,
                "total_cost": 20,
                "currency": "USD",
            },
        },
    ]


def test_compute_purchase_cost_by_location(sample_telemetry_rows):
    """Costo de compra por local = sum of inbound_order_created costs."""
    result = compute_purchase_cost_by_location(_events_frame(sample_telemetry_rows))
    assert result["1"] == 10000.0
    assert result["2"] == 20.0


def test_compute_waste_cost_and_ratio_matches_context_definition(sample_telemetry_rows):
    """Costo de merma + Ratio de merma = waste / purchase (CONTEXT definition)."""
    df = _events_frame(sample_telemetry_rows)
    purchase = compute_purchase_cost_by_location(df)
    waste = compute_waste_cost_by_location(df)
    assert waste["1"] == 1000.0
    # Manual CONTEXT check: 1000 / 10000 = 0.1
    assert compute_waste_ratio(purchase["1"], waste["1"]) == 0.1
    assert compute_waste_ratio(0, 500) == 0.0


def test_compute_stockout_and_price_alert_frequencies(sample_telemetry_rows):
    """Frecuencia de quiebre de stock + Frecuencia de alertas de precio."""
    df = _events_frame(sample_telemetry_rows)
    assert compute_stockout_events_by_location(df)["1"] == 1
    assert compute_price_alert_events_by_location(df)["1"] == 1
    assert compute_stockout_events_by_location(df).get("2", 0) == 0


def test_refine_and_aggregate_assembles_all_context_kpis(sample_telemetry_rows):
    rows = refine_and_aggregate(
        _events_frame(sample_telemetry_rows), date(2026, 8, 24)
    )
    by_loc = {r["location_id"]: r for r in rows}
    assert by_loc["1"]["total_purchase_cost"] == 10000.0
    assert by_loc["1"]["total_waste_cost"] == 1000.0
    assert by_loc["1"]["waste_ratio"] == 0.1
    assert by_loc["1"]["stockout_events_count"] == 1
    assert by_loc["1"]["price_alert_events_count"] == 1
    assert by_loc["1"]["currency"] == "COP"
    assert by_loc["2"]["currency"] == "USD"


def test_defensive_line_cost_and_malformed_tags():
    """Invalid / missing cost fields must not raise; cost falls back to 0."""
    assert line_cost_from_tags(None) == 0.0
    assert line_cost_from_tags("not-a-dict") == 0.0  # type: ignore[arg-type]
    assert line_cost_from_tags({"total_cost": "nope"}) == 0.0
    assert line_cost_from_tags({"quantity": "x", "unit_cost": 10}) == 0.0
    assert line_cost_from_tags({"quantity": 2, "unit_cost": 5}) == 10.0

    malformed = pd.DataFrame(
        [
            {
                "event_id": "bad1",
                "event_type": "inbound_order_created",
                "timestamp": "not-a-date",
                "tags": "{broken",
            },
            {
                "event_id": "bad2",
                "event_type": "inbound_order_created",
                "timestamp": "2026-08-24T12:00:00Z",
                "tags": {"country": "CO"},  # missing location_id → dropped
            },
        ]
    )
    assert refine_and_aggregate(malformed, date(2026, 8, 24)) == []
    assert compute_purchase_cost_by_location(malformed) == {}
