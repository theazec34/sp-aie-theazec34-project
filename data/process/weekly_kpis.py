"""Pure transforms for weekly location cost & waste KPIs (no I/O)."""

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


def _parse_tags(raw: Any) -> dict[str, Any]:
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


def _line_cost(tags: dict[str, Any]) -> float:
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


def refine_and_aggregate(
    events: pd.DataFrame,
    week_start: date,
) -> list[dict[str, Any]]:
    """Build one KPI row per location_id for ``week_start``.

    Expects columns: event_id, event_type, timestamp, tags.
    """
    if events is None or events.empty:
        return []

    df = events.copy()
    df = df.drop_duplicates(subset=["event_id"], keep="first")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    tags = df["tags"].map(_parse_tags)
    df["location_id"] = tags.map(
        lambda t: str(t["location_id"]) if t.get("location_id") is not None else None
    )
    df["country"] = tags.map(lambda t: t.get("country"))
    df["line_cost"] = tags.map(_line_cost)
    df = df.dropna(subset=["location_id"])
    if df.empty:
        return []

    # Prefer country from tags; default CO if missing
    df["country"] = df["country"].fillna("CO").astype(str).str.upper()
    df.loc[~df["country"].isin(["CO", "US"]), "country"] = "CO"

    locations = sorted(df["location_id"].unique())
    rows: list[dict[str, Any]] = []
    for loc in locations:
        part = df[df["location_id"] == loc]
        country = str(part["country"].mode().iloc[0])
        purchase = float(
            part.loc[part["event_type"] == "inbound_order_created", "line_cost"].sum()
        )
        waste = float(
            part.loc[part["event_type"] == "stock_waste_registered", "line_cost"].sum()
        )
        ratio = (waste / purchase) if purchase > 0 else 0.0
        stockouts = int((part["event_type"] == "stock_threshold_triggered").sum())
        price_alerts = int(
            (part["event_type"] == "ingredient_price_variance_detected").sum()
        )
        rows.append(
            {
                "location_id": str(loc),
                "country": country,
                "week_start": week_start.isoformat(),
                "total_purchase_cost": round(purchase, 4),
                "total_waste_cost": round(waste, 4),
                "waste_ratio": round(ratio, 6),
                "stockout_events_count": stockouts,
                "price_alert_events_count": price_alerts,
                "currency": currency_for_country(country),
            }
        )
    return rows
