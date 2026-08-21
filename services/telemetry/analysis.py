"""Telemetry analysis pipeline — Load (SQL) → Refine (Pandas) → Group → Aggregate.

Canonical path for this milestone: ``services/telemetry/analysis.py``.
Metrics are pure functions: no loops for aggregation; timestamps → UTC datetime
before any temporal groupby.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

# Technical / operational error-like event types (not business KPIs).
ERROR_EVENT_TYPES = frozenset(
    {
        "frontend_error_captured",
        "auth_login_failed",
        "auth_session_expired",
        "outbound_order_rejected",
        "inventory_validation_failed",
        "direct_stock_edit_rejected",
    }
)

AUTH_EVENT_TYPES = ("auth_login_failed", "auth_login_succeeded")


def default_period(
    start_date: date | None = None,
    end_date: date | None = None,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime, date, date]:
    """Resolve inclusive calendar dates → half-open UTC window [start, end).

    Defaults to the last 7 UTC days ending at tomorrow 00:00 (so today is included).
    Returns (start_dt, end_dt, period_from, period_to) where period_* are inclusive
    dates for the JSON response.
    """
    now = now or datetime.now(timezone.utc)
    today = now.date()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=6)
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
    # exclusive end = day after inclusive end_date
    end_exclusive = end_date + timedelta(days=1)
    end_dt = datetime(
        end_exclusive.year, end_exclusive.month, end_exclusive.day, tzinfo=timezone.utc
    )
    return start_dt, end_dt, start_date, end_date


def load_events(
    engine: Engine,
    start: datetime,
    end: datetime,
    event_types: list[str] | tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """SQL load — filter timestamp (and optional event_type) only; never SELECT * unbounded."""
    sql = """
        SELECT event_id, event_type, timestamp, service, session_id, user_id, tags
        FROM telemetry_events
        WHERE timestamp >= :start AND timestamp < :end
    """
    params: dict[str, Any] = {"start": start, "end": end}
    if event_types:
        sql += " AND event_type IN :types"
        stmt = text(sql).bindparams(bindparam("types", expanding=True))
        params["types"] = list(event_types)
    else:
        stmt = text(sql)
    with engine.connect() as conn:
        df = pd.read_sql(stmt, conn, params=params)
    return df


def _ensure_timestamp_utc(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)
    out["date"] = out["timestamp"].dt.strftime("%Y-%m-%d")
    return out


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


def events_per_day(
    engine: Engine,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """Volume: ¿cuántos eventos de telemetría llegan por día?

    AGGREGATION = count(event_id) grouped by date.
    """
    df = _ensure_timestamp_utc(load_events(engine, start, end))
    if df.empty:
        return []
    out = (
        df.groupby("date", as_index=False)
        .agg(count=("event_id", "count"))
        .sort_values("date")
    )
    return out.to_dict(orient="records")


def error_rate_by_type(
    engine: Engine,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """Errors: ¿qué proporción del tráfico diario es cada tipo de error técnico?

    Loads all events in the window (needed for daily denominator), flags errors in
    Pandas, then rate = error_count / daily_total per (date, event_type).
    """
    df = _ensure_timestamp_utc(load_events(engine, start, end))
    if df.empty:
        return []
    df = df.copy()
    df["is_error"] = df["event_type"].isin(ERROR_EVENT_TYPES)
    daily_total = df.groupby("date")["event_id"].transform("count")
    errors = df.loc[df["is_error"]].copy()
    if errors.empty:
        return []
    errors["daily_total"] = daily_total.loc[errors.index]
    grouped = (
        errors.groupby(["date", "event_type"], as_index=False)
        .agg(error_count=("event_id", "count"), daily_total=("daily_total", "max"))
        .sort_values(["date", "event_type"])
    )
    grouped["rate"] = (grouped["error_count"] / grouped["daily_total"]).round(4)
    return grouped.to_dict(orient="records")


def auth_failure_rate(
    engine: Engine,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """Auth: ¿qué % de intentos de login fallan cada día?

    rate = auth_login_failed / (auth_login_failed + auth_login_succeeded)
    (event names match Brasaland capture instrumentation).
    """
    df = _ensure_timestamp_utc(
        load_events(engine, start, end, event_types=AUTH_EVENT_TYPES)
    )
    if df.empty:
        return []
    pivot = (
        df.groupby(["date", "event_type"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in AUTH_EVENT_TYPES:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot["attempts"] = pivot["auth_login_failed"] + pivot["auth_login_succeeded"]
    pivot["rate"] = 0.0
    mask = pivot["attempts"] > 0
    pivot.loc[mask, "rate"] = (
        pivot.loc[mask, "auth_login_failed"] / pivot.loc[mask, "attempts"]
    ).round(4)
    out = pivot.rename(
        columns={
            "auth_login_failed": "failed",
            "auth_login_succeeded": "succeeded",
        }
    )[["date", "failed", "succeeded", "attempts", "rate"]].sort_values("date")
    return out.to_dict(orient="records")


def latency_by_route(
    engine: Engine,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    """Latency: ¿cuál es la latencia media diaria por ruta de API?

    Uses ``api_latency_recorded``; route and duration_ms come from tags.
    """
    df = _ensure_timestamp_utc(
        load_events(engine, start, end, event_types=["api_latency_recorded"])
    )
    if df.empty:
        return []
    tags = df["tags"].map(_parse_tags)
    refined = df.assign(
        route=tags.map(lambda t: t.get("route")),
        duration_ms=tags.map(lambda t: t.get("duration_ms")),
    )
    refined = refined.dropna(subset=["route", "duration_ms"])
    if refined.empty:
        return []
    refined["duration_ms"] = pd.to_numeric(refined["duration_ms"], errors="coerce")
    refined = refined.dropna(subset=["duration_ms"])
    out = (
        refined.groupby(["date", "route"], as_index=False)
        .agg(
            avg_duration_ms=("duration_ms", "mean"),
            samples=("duration_ms", "count"),
        )
        .sort_values(["date", "route"])
    )
    out["avg_duration_ms"] = out["avg_duration_ms"].round(2)
    return out.to_dict(orient="records")


def build_report(
    engine: Engine,
    start: datetime,
    end: datetime,
    *,
    period_from: date,
    period_to: date,
) -> dict[str, Any]:
    """Run all metric pipelines once; endpoint caches this result."""
    return {
        "period": {
            "from": period_from.isoformat(),
            "to": period_to.isoformat(),
        },
        "metrics": {
            "events_per_day": events_per_day(engine, start, end),
            "error_rate_by_type": error_rate_by_type(engine, start, end),
            "auth_failure_rate": auth_failure_rate(engine, start, end),
            "latency_by_route": latency_by_route(engine, start, end),
        },
    }
