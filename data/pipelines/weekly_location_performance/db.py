"""Reporting DB helpers: ensure tables, upsert KPIs, pipeline run log, queries.

Postgres uses schema ``reporting``; SQLite uses the same table names without schema
(compatible with the local inventory/telemetry SQLite fallback).
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_ROOT = _REPO_ROOT / "services" / "api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.database import engine as _default_engine  # noqa: E402


def get_engine() -> Engine:
    return _default_engine


def _is_postgres(eng: Engine) -> bool:
    return eng.dialect.name == "postgresql"


def perf_table(eng: Engine) -> str:
    return (
        "reporting.weekly_location_performance"
        if _is_postgres(eng)
        else "weekly_location_performance"
    )


def run_log_table(eng: Engine) -> str:
    return "reporting.pipeline_run_log" if _is_postgres(eng) else "pipeline_run_log"


def ensure_reporting_tables(eng: Engine | None = None) -> None:
    eng = eng or get_engine()
    with eng.begin() as conn:
        if _is_postgres(eng):
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS reporting"))
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS reporting.weekly_location_performance (
                      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                      location_id text NOT NULL,
                      country text NOT NULL,
                      week_start date NOT NULL,
                      total_purchase_cost numeric NOT NULL DEFAULT 0,
                      total_waste_cost numeric NOT NULL DEFAULT 0,
                      waste_ratio numeric NOT NULL DEFAULT 0,
                      stockout_events_count integer NOT NULL DEFAULT 0,
                      price_alert_events_count integer NOT NULL DEFAULT 0,
                      currency text NOT NULL,
                      computed_at timestamptz NOT NULL DEFAULT now(),
                      UNIQUE (location_id, week_start)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS reporting.pipeline_run_log (
                      run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                      pipeline_name text NOT NULL,
                      week_start date NOT NULL,
                      status text NOT NULL,
                      started_at timestamptz NOT NULL,
                      finished_at timestamptz,
                      rows_extracted integer NOT NULL DEFAULT 0,
                      rows_upserted integer NOT NULL DEFAULT 0,
                      error_message text,
                      triggered_by text NOT NULL DEFAULT 'scheduler',
                      checkpoint jsonb NOT NULL DEFAULT '{}'::jsonb
                    )
                    """
                )
            )
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS weekly_location_performance (
                      id TEXT PRIMARY KEY,
                      location_id TEXT NOT NULL,
                      country TEXT NOT NULL,
                      week_start TEXT NOT NULL,
                      total_purchase_cost REAL NOT NULL DEFAULT 0,
                      total_waste_cost REAL NOT NULL DEFAULT 0,
                      waste_ratio REAL NOT NULL DEFAULT 0,
                      stockout_events_count INTEGER NOT NULL DEFAULT 0,
                      price_alert_events_count INTEGER NOT NULL DEFAULT 0,
                      currency TEXT NOT NULL,
                      computed_at TEXT NOT NULL,
                      UNIQUE (location_id, week_start)
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS pipeline_run_log (
                      run_id TEXT PRIMARY KEY,
                      pipeline_name TEXT NOT NULL,
                      week_start TEXT NOT NULL,
                      status TEXT NOT NULL,
                      started_at TEXT NOT NULL,
                      finished_at TEXT,
                      rows_extracted INTEGER NOT NULL DEFAULT 0,
                      rows_upserted INTEGER NOT NULL DEFAULT 0,
                      error_message TEXT,
                      triggered_by TEXT NOT NULL DEFAULT 'scheduler',
                      checkpoint TEXT NOT NULL DEFAULT '{}'
                    )
                    """
                )
            )


def open_run(
    *,
    pipeline_name: str,
    week_start: date,
    triggered_by: str,
    eng: Engine | None = None,
) -> str:
    eng = eng or get_engine()
    ensure_reporting_tables(eng)
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    tbl = run_log_table(eng)
    with eng.begin() as conn:
        if _is_postgres(eng):
            conn.execute(
                text(
                    f"""
                    INSERT INTO {tbl}
                    (run_id, pipeline_name, week_start, status, started_at, triggered_by, checkpoint)
                    VALUES (:run_id, :pipeline_name, :week_start, 'running', now(), :triggered_by, '{{}}'::jsonb)
                    """
                ),
                {
                    "run_id": run_id,
                    "pipeline_name": pipeline_name,
                    "week_start": week_start,
                    "triggered_by": triggered_by,
                },
            )
        else:
            conn.execute(
                text(
                    f"""
                    INSERT INTO {tbl}
                    (run_id, pipeline_name, week_start, status, started_at, triggered_by, checkpoint)
                    VALUES (:run_id, :pipeline_name, :week_start, 'running', :started_at, :triggered_by, '{{}}')
                    """
                ),
                {
                    "run_id": run_id,
                    "pipeline_name": pipeline_name,
                    "week_start": week_start.isoformat(),
                    "started_at": now,
                    "triggered_by": triggered_by,
                },
            )
    return run_id


def finish_run(
    run_id: str,
    *,
    status: str,
    rows_extracted: int = 0,
    rows_upserted: int = 0,
    error_message: str | None = None,
    checkpoint: dict[str, Any] | None = None,
    eng: Engine | None = None,
) -> None:
    eng = eng or get_engine()
    tbl = run_log_table(eng)
    cp = json.dumps(checkpoint or {})
    with eng.begin() as conn:
        if _is_postgres(eng):
            conn.execute(
                text(
                    f"""
                    UPDATE {tbl}
                    SET status = :status,
                        finished_at = now(),
                        rows_extracted = :rows_extracted,
                        rows_upserted = :rows_upserted,
                        error_message = :error_message,
                        checkpoint = CAST(:checkpoint AS jsonb)
                    WHERE run_id = CAST(:run_id AS uuid)
                    """
                ),
                {
                    "run_id": run_id,
                    "status": status,
                    "rows_extracted": rows_extracted,
                    "rows_upserted": rows_upserted,
                    "error_message": error_message,
                    "checkpoint": cp,
                },
            )
        else:
            conn.execute(
                text(
                    f"""
                    UPDATE {tbl}
                    SET status = :status,
                        finished_at = :finished_at,
                        rows_extracted = :rows_extracted,
                        rows_upserted = :rows_upserted,
                        error_message = :error_message,
                        checkpoint = :checkpoint
                    WHERE run_id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "status": status,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "rows_extracted": rows_extracted,
                    "rows_upserted": rows_upserted,
                    "error_message": error_message,
                    "checkpoint": cp,
                },
            )


def upsert_kpi_rows(
    rows: list[dict[str, Any]],
    *,
    eng: Engine | None = None,
) -> int:
    """Idempotent load: UNIQUE(location_id, week_start) UPSERT."""
    eng = eng or get_engine()
    ensure_reporting_tables(eng)
    if not rows:
        return 0
    tbl = perf_table(eng)
    now = datetime.now(timezone.utc).isoformat()
    with eng.begin() as conn:
        for row in rows:
            if _is_postgres(eng):
                conn.execute(
                    text(
                        f"""
                        INSERT INTO {tbl}
                        (location_id, country, week_start, total_purchase_cost, total_waste_cost,
                         waste_ratio, stockout_events_count, price_alert_events_count, currency, computed_at)
                        VALUES
                        (:location_id, :country, :week_start, :total_purchase_cost, :total_waste_cost,
                         :waste_ratio, :stockout_events_count, :price_alert_events_count, :currency, now())
                        ON CONFLICT (location_id, week_start) DO UPDATE SET
                          country = EXCLUDED.country,
                          total_purchase_cost = EXCLUDED.total_purchase_cost,
                          total_waste_cost = EXCLUDED.total_waste_cost,
                          waste_ratio = EXCLUDED.waste_ratio,
                          stockout_events_count = EXCLUDED.stockout_events_count,
                          price_alert_events_count = EXCLUDED.price_alert_events_count,
                          currency = EXCLUDED.currency,
                          computed_at = now()
                        """
                    ),
                    row,
                )
            else:
                conn.execute(
                    text(
                        f"""
                        INSERT INTO {tbl}
                        (id, location_id, country, week_start, total_purchase_cost, total_waste_cost,
                         waste_ratio, stockout_events_count, price_alert_events_count, currency, computed_at)
                        VALUES
                        (:id, :location_id, :country, :week_start, :total_purchase_cost, :total_waste_cost,
                         :waste_ratio, :stockout_events_count, :price_alert_events_count, :currency, :computed_at)
                        ON CONFLICT (location_id, week_start) DO UPDATE SET
                          country = excluded.country,
                          total_purchase_cost = excluded.total_purchase_cost,
                          total_waste_cost = excluded.total_waste_cost,
                          waste_ratio = excluded.waste_ratio,
                          stockout_events_count = excluded.stockout_events_count,
                          price_alert_events_count = excluded.price_alert_events_count,
                          currency = excluded.currency,
                          computed_at = excluded.computed_at
                        """
                    ),
                    {
                        **row,
                        "id": str(uuid.uuid4()),
                        "computed_at": now,
                    },
                )
    return len(rows)


def query_weekly_location_performance(
    week_start: date | None = None,
    *,
    eng: Engine | None = None,
) -> dict[str, Any]:
    eng = eng or get_engine()
    ensure_reporting_tables(eng)
    tbl = perf_table(eng)
    with eng.connect() as conn:
        if week_start is None:
            if _is_postgres(eng):
                latest = conn.execute(
                    text(f"SELECT max(week_start) FROM {tbl}")
                ).scalar()
            else:
                latest = conn.execute(
                    text(f"SELECT max(week_start) FROM {tbl}")
                ).scalar()
            if latest is None:
                day = datetime.now(timezone.utc).date()
                week_start = day - timedelta(days=day.weekday())
            else:
                week_start = (
                    latest if isinstance(latest, date) else date.fromisoformat(str(latest))
                )
        ws = week_start.isoformat() if isinstance(week_start, date) else str(week_start)
        result = conn.execute(
            text(
                f"""
                SELECT location_id, country, total_purchase_cost, total_waste_cost, waste_ratio,
                       stockout_events_count, price_alert_events_count, currency
                FROM {tbl}
                WHERE week_start = :week_start
                ORDER BY country, location_id
                """
            ),
            {"week_start": week_start if _is_postgres(eng) else ws},
        )
        locations = []
        for r in result.mappings():
            locations.append(
                {
                    "location_id": str(r["location_id"]),
                    "country": r["country"],
                    "total_purchase_cost": float(r["total_purchase_cost"] or 0),
                    "total_waste_cost": float(r["total_waste_cost"] or 0),
                    "waste_ratio": float(r["waste_ratio"] or 0),
                    "stockout_events_count": int(r["stockout_events_count"] or 0),
                    "price_alert_events_count": int(r["price_alert_events_count"] or 0),
                    "currency": r["currency"],
                }
            )
    return {"week_start": ws if isinstance(week_start, date) else str(week_start), "locations": locations}


def get_latest_run(
    pipeline_name: str = "weekly_location_performance",
    *,
    eng: Engine | None = None,
) -> dict[str, Any] | None:
    eng = eng or get_engine()
    ensure_reporting_tables(eng)
    tbl = run_log_table(eng)
    with eng.connect() as conn:
        row = conn.execute(
            text(
                f"""
                SELECT run_id, pipeline_name, week_start, status, started_at, finished_at,
                       rows_extracted, rows_upserted, error_message, triggered_by
                FROM {tbl}
                WHERE pipeline_name = :pipeline_name
                ORDER BY started_at DESC
                LIMIT 1
                """
            ),
            {"pipeline_name": pipeline_name},
        ).mappings().first()
    if not row:
        return None
    return {
        "run_id": str(row["run_id"]),
        "pipeline_name": row["pipeline_name"],
        "week_start": str(row["week_start"]),
        "status": row["status"],
        "started_at": str(row["started_at"]),
        "finished_at": str(row["finished_at"]) if row["finished_at"] else None,
        "rows_extracted": int(row["rows_extracted"] or 0),
        "rows_upserted": int(row["rows_upserted"] or 0),
        "error_message": row["error_message"],
        "triggered_by": row["triggered_by"],
    }
