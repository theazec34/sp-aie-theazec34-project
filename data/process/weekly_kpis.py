"""Pure transforms for weekly location cost & waste KPIs (no I/O).

KPI names match CONTEXT «KPIs a medir»:
- total_purchase_cost → Costo de compra por local
- total_waste_cost → Costo de merma por local
- waste_ratio → Ratio de merma
- stockout_events_count → Frecuencia de quiebre de stock
- price_alert_events_count → Frecuencia de alertas de precio
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd

KPI_EVENT_TYPES = (
    "inbound_order_created",
    "stock_waste_registered",
    "stock_threshold_triggered",
    "ingredient_price_variance_detected",
)

PIPELINE_NAME = "weekly_location_performance"


def iso_week_start(day: date | None = None) -> date:
    """Monday (UTC) of the ISO week containing ``day`` (default: today UTC)."""
    day = day or datetime.now(timezone.utc).date()
    return day - timedelta(days=day.weekday())


def week_window(week_start: date) -> tuple[datetime, datetime]:
    """Half-open UTC window [week_start, week_start+7d)."""
    start = datetime(week_start.year, week_start.month, week_start.day, tzinfo=timezone.utc)
    end = start + timedelta(days=7)
    return start, end


def currency_for_country(country: str) -> str:
    return "USD" if str(country).upper() == "US" else "COP"


def parse_tags(raw: Any) -> dict[str, Any]:
    """Defensive parse of telemetry ``tags`` / properties blob."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def line_cost_from_tags(tags: dict[str, Any] | None) -> float:
    """Line monetary cost: prefer ``total_cost``, else ``quantity * unit_cost``.

    Malformed / missing values yield 0.0 (never raise) so aggregates stay defined.
    """
    if not isinstance(tags, dict):
        return 0.0
    if tags.get("total_cost") is not None:
        try:
            return float(tags["total_cost"])
        except (TypeError, ValueError):
            pass
    qty = tags.get("quantity")
    unit = tags.get("unit_cost")
    if qty is None or unit is None:
        return 0.0
    try:
        return float(qty) * float(unit)
    except (TypeError, ValueError):
        return 0.0


def _prepare_event_frame(events: pd.DataFrame) -> pd.DataFrame:
    if events is None or events.empty:
        return pd.DataFrame()
    df = events.copy()
    if "event_id" in df.columns:
        df = df.drop_duplicates(subset=["event_id"], keep="first")
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    tags = df["tags"].map(parse_tags) if "tags" in df.columns else pd.Series([{}] * len(df))
    df["location_id"] = tags.map(
        lambda t: str(t["location_id"]) if t.get("location_id") is not None else None
    )
    df["country"] = tags.map(lambda t: t.get("country"))
    df["line_cost"] = tags.map(line_cost_from_tags)
    df = df.dropna(subset=["location_id"])
    if df.empty:
        return df
    df["country"] = df["country"].fillna("CO").astype(str).str.upper()
    df.loc[~df["country"].isin(["CO", "US"]), "country"] = "CO"
    return df


def compute_purchase_cost_by_location(events: pd.DataFrame) -> dict[str, float]:
    """KPI: Costo de compra por local — sum of inbound_order_created line costs."""
    df = _prepare_event_frame(events)
    if df.empty:
        return {}
    part = df[df["event_type"] == "inbound_order_created"]
    if part.empty:
        return {str(loc): 0.0 for loc in df["location_id"].unique()}
    totals = part.groupby("location_id")["line_cost"].sum()
    return {str(k): round(float(v), 4) for k, v in totals.items()}


def compute_waste_cost_by_location(events: pd.DataFrame) -> dict[str, float]:
    """KPI: Costo de merma por local — sum of stock_waste_registered line costs."""
    df = _prepare_event_frame(events)
    if df.empty:
        return {}
    part = df[df["event_type"] == "stock_waste_registered"]
    if part.empty:
        return {str(loc): 0.0 for loc in df["location_id"].unique()}
    totals = part.groupby("location_id")["line_cost"].sum()
    return {str(k): round(float(v), 4) for k, v in totals.items()}


def compute_waste_ratio(purchase: float, waste: float) -> float:
    """KPI: Ratio de merma = waste / purchase (0 if no purchases that week)."""
    try:
        purchase_f = float(purchase)
        waste_f = float(waste)
    except (TypeError, ValueError):
        return 0.0
    if purchase_f <= 0:
        return 0.0
    return round(waste_f / purchase_f, 6)


def compute_stockout_events_by_location(events: pd.DataFrame) -> dict[str, int]:
    """KPI: Frecuencia de quiebre de stock — count stock_threshold_triggered."""
    df = _prepare_event_frame(events)
    if df.empty:
        return {}
    part = df[df["event_type"] == "stock_threshold_triggered"]
    counts = part.groupby("location_id").size() if not part.empty else pd.Series(dtype=int)
    result = {str(loc): 0 for loc in df["location_id"].unique()}
    for loc, n in counts.items():
        result[str(loc)] = int(n)
    return result


def compute_price_alert_events_by_location(events: pd.DataFrame) -> dict[str, int]:
    """KPI: Frecuencia de alertas de precio — count ingredient_price_variance_detected."""
    df = _prepare_event_frame(events)
    if df.empty:
        return {}
    part = df[df["event_type"] == "ingredient_price_variance_detected"]
    counts = part.groupby("location_id").size() if not part.empty else pd.Series(dtype=int)
    result = {str(loc): 0 for loc in df["location_id"].unique()}
    for loc, n in counts.items():
        result[str(loc)] = int(n)
    return result


def refine_and_aggregate(
    events: pd.DataFrame,
    week_start: date,
) -> list[dict[str, Any]]:
    """Build one KPI row per location_id for ``week_start``."""
    df = _prepare_event_frame(events)
    if df.empty:
        return []

    purchase = compute_purchase_cost_by_location(df)
    waste = compute_waste_cost_by_location(df)
    stockouts = compute_stockout_events_by_location(df)
    alerts = compute_price_alert_events_by_location(df)

    locations = sorted(df["location_id"].unique())
    rows: list[dict[str, Any]] = []
    for loc in locations:
        part = df[df["location_id"] == loc]
        country = str(part["country"].mode().iloc[0])
        p = float(purchase.get(str(loc), 0.0))
        w = float(waste.get(str(loc), 0.0))
        rows.append(
            {
                "location_id": str(loc),
                "country": country,
                "week_start": week_start.isoformat(),
                "total_purchase_cost": p,
                "total_waste_cost": w,
                "waste_ratio": compute_waste_ratio(p, w),
                "stockout_events_count": int(stockouts.get(str(loc), 0)),
                "price_alert_events_count": int(alerts.get(str(loc), 0)),
                "currency": currency_for_country(country),
            }
        )
    return rows
