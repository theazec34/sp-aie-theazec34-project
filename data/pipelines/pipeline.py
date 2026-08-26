"""
Brasaland — weekly location performance pipeline (Prefect 3).

Cadence (design): weekly, ready Monday morning UTC (schedule target Mon 05:00 UTC).
CLI (required by hito):

    python data/pipelines/pipeline.py
    python data/pipelines/pipeline.py --week-start 2026-08-17

Flow name and tasks match data/pipelines/PIPELINE_DESIGN.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from prefect import flow, task
from prefect.cache_policies import INPUTS
from sqlalchemy import bindparam, text

# Monorepo roots on sys.path: repo root (data.*) + services/api (app.*)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
for _p in (_REPO_ROOT, _API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.process.weekly_kpis import (  # noqa: E402
    KPI_EVENT_TYPES,
    PIPELINE_NAME,
    iso_week_start,
    refine_and_aggregate,
    week_window,
)
from data.pipelines.weekly_location_performance.db import (  # noqa: E402
    ensure_reporting_tables,
    finish_run,
    get_engine,
    open_run,
    upsert_kpi_rows,
)

_RAW_DIR = _REPO_ROOT / "data" / "raw"
_EVAL_DIR = _REPO_ROOT / "data" / "eval"


@task(
    name="extract_telemetry_week",
    # Retries=3: absorb transient DB pool / network blips against Supabase (external).
    retries=3,
    retry_delay_seconds=5,
)
def extract_telemetry_week(week_start: date) -> dict:
    """Extract KPI events for the ISO week from telemetry_events (read-only)."""
    eng = get_engine()
    start, end = week_window(week_start)
    # Ensure telemetry table exists when running against fresh SQLite.
    from app.database import init_db
    from app.telemetry import orm as _telemetry_orm  # noqa: F401

    init_db()
    ensure_reporting_tables(eng)

    sql = """
        SELECT event_id, event_type, timestamp, tags
        FROM telemetry_events
        WHERE timestamp >= :start AND timestamp < :end
          AND event_type IN :types
    """
    stmt = text(sql).bindparams(bindparam("types", expanding=True))
    with eng.connect() as conn:
        df = pd.read_sql(
            stmt,
            conn,
            params={"start": start, "end": end, "types": list(KPI_EVENT_TYPES)},
        )

    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = _RAW_DIR / f"telemetry_week_{week_start.isoformat()}.parquet"
    try:
        df.to_parquet(raw_path, index=False)
    except Exception:
        # Parquet optional (pyarrow may be missing); fall back to CSV.
        raw_path = _RAW_DIR / f"telemetry_week_{week_start.isoformat()}.csv"
        df.to_csv(raw_path, index=False)

    return {
        "week_start": week_start.isoformat(),
        "rows": df.to_dict(orient="records"),
        "rows_extracted": int(len(df)),
        "raw_path": str(raw_path),
    }


@task(
    name="transform_location_kpis",
    # Cache key = task inputs (week_start + extracted payload hash via INPUTS).
    # Expiration 1h: skip expensive re-aggregation when re-triggered within the hour.
    cache_policy=INPUTS,
    cache_expiration=timedelta(hours=1),
)
def transform_location_kpis(extract_result: dict) -> dict:
    """Refine tags and aggregate CONTEXT KPIs per location_id × week_start."""
    week_start = date.fromisoformat(extract_result["week_start"])
    df = pd.DataFrame(extract_result.get("rows") or [])
    rows = refine_and_aggregate(df, week_start)
    return {
        "week_start": week_start.isoformat(),
        "kpi_rows": rows,
        "rows_extracted": int(extract_result.get("rows_extracted") or 0),
    }


@task(
    name="load_weekly_location_performance",
    # Retries=3: Load hits Postgres/SQLite; brief locks/timeouts should not fail the week.
    retries=3,
    retry_delay_seconds=5,
)
def load_weekly_location_performance(transform_result: dict, run_id: str) -> dict:
    """Idempotent UPSERT into reporting.weekly_location_performance."""
    rows = transform_result.get("kpi_rows") or []
    upserted = upsert_kpi_rows(rows)
    finish_run(
        run_id,
        status="completed",
        rows_extracted=int(transform_result.get("rows_extracted") or 0),
        rows_upserted=upserted,
        checkpoint={
            "week_start": transform_result.get("week_start"),
            "stage": "load",
            "locations_done": [r["location_id"] for r in rows],
        },
    )
    return {
        "rows_upserted": upserted,
        "week_start": transform_result.get("week_start"),
        "run_id": run_id,
    }


@task(name="write_eval_snapshot")
def write_eval_snapshot(transform_result: dict, load_result: dict) -> str:
    """Optional non-critical eval artifact under data/eval/."""
    _EVAL_DIR.mkdir(parents=True, exist_ok=True)
    path = _EVAL_DIR / f"weekly_kpis_{transform_result['week_start']}.json"
    payload = {
        "week_start": transform_result.get("week_start"),
        "kpi_rows": transform_result.get("kpi_rows"),
        "rows_upserted": load_result.get("rows_upserted"),
        "written_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


@flow(name="weekly_location_performance_flow")
def weekly_location_performance_flow(
    week_start: date | None = None,
    triggered_by: str = "scheduler",
) -> dict:
    """Main business performance ETL: extract → transform → load (+ optional eval)."""
    week_start = week_start or iso_week_start()
    ensure_reporting_tables()
    run_id = open_run(
        pipeline_name=PIPELINE_NAME,
        week_start=week_start,
        triggered_by=triggered_by,
    )
    try:
        extracted = extract_telemetry_week(week_start)
        transformed = transform_location_kpis(extracted)
        loaded = load_weekly_location_performance(transformed, run_id)

        # Optional step: failure must not abort the main ETL (return_state=True).
        eval_state = write_eval_snapshot(transformed, loaded, return_state=True)
        eval_ok = eval_state is not None and eval_state.is_completed()
        eval_path = eval_state.result() if eval_ok else None
        if not eval_ok:
            # Logged via Prefect state; flow continues as Completed.
            pass

        return {
            "run_id": run_id,
            "status": "completed",
            "week_start": week_start.isoformat(),
            "rows_extracted": transformed.get("rows_extracted", 0),
            "rows_upserted": loaded.get("rows_upserted", 0),
            "eval_snapshot": eval_path,
            "eval_ok": eval_ok,
        }
    except Exception as exc:  # noqa: BLE001
        finish_run(
            run_id,
            status="failed",
            error_message=str(exc)[:500],
            checkpoint={"week_start": week_start.isoformat(), "stage": "failed"},
        )
        raise


def trigger_weekly_location_performance_flow(
    week_start: date | None = None,
    triggered_by: str = "api_manual",
) -> dict:
    """API-facing entrypoint (no ETL logic in services/)."""
    result = weekly_location_performance_flow(
        week_start=week_start,
        triggered_by=triggered_by,
    )
    return result if isinstance(result, dict) else {"status": "completed", "result": str(result)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run weekly_location_performance_flow")
    parser.add_argument(
        "--week-start",
        type=str,
        default=None,
        help="ISO Monday YYYY-MM-DD (default: current UTC ISO week)",
    )
    parser.add_argument(
        "--triggered-by",
        type=str,
        default="cli",
        help="Audit label for pipeline_run_log.triggered_by",
    )
    args = parser.parse_args(argv)
    week = date.fromisoformat(args.week_start) if args.week_start else None
    out = weekly_location_performance_flow(week_start=week, triggered_by=args.triggered_by)
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
