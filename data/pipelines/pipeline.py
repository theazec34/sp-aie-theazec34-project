"""
Brasaland — weekly location performance pipeline (Prefect 3).

Cadence (design): weekly, ready Monday morning UTC (schedule target Mon 05:00 UTC).
CLI (required by hito):

    python data/pipelines/pipeline.py
    python data/pipelines/pipeline.py --week-start 2026-08-17

Part 3: main flow coordinates domain subflows (extract / transform / load / eval).
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

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
for _p in (_REPO_ROOT, _API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.process.weekly_kpis import (  # noqa: E402
    KPI_EVENT_TYPES,
    PIPELINE_NAME,
    compute_price_alert_events_by_location,
    compute_purchase_cost_by_location,
    compute_stockout_events_by_location,
    compute_waste_cost_by_location,
    compute_waste_ratio,
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


# ---------------------------------------------------------------------------
# Tasks (called from subflows — domain vocabulary from CONTEXT KPIs)
# ---------------------------------------------------------------------------


@task(
    name="extract_telemetry_events_for_cost_waste_week",
    # Retries=3: absorb transient DB pool / network blips against Supabase (external).
    retries=3,
    retry_delay_seconds=5,
)
def extract_telemetry_events_for_cost_waste_week(week_start: date) -> dict:
    """Read-only extract of KPI events from telemetry_events for one ISO week."""
    eng = get_engine()
    start, end = week_window(week_start)
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
    raw_path = _RAW_DIR / f"telemetry_week_{week_start.isoformat()}.csv"
    df.to_csv(raw_path, index=False)

    return {
        "week_start": week_start.isoformat(),
        "rows": df.to_dict(orient="records"),
        "rows_extracted": int(len(df)),
        "raw_path": str(raw_path),
    }


@task(name="compute_purchase_cost_by_location_task")
def compute_purchase_cost_by_location_task(rows: list[dict]) -> dict[str, float]:
    """Transform task: Costo de compra por local."""
    return compute_purchase_cost_by_location(pd.DataFrame(rows))


@task(name="compute_waste_cost_and_ratio_by_location_task")
def compute_waste_cost_and_ratio_by_location_task(
    rows: list[dict],
    purchase_by_location: dict[str, float],
) -> dict[str, dict[str, float]]:
    """Transform task: Costo de merma + Ratio de merma por local."""
    waste = compute_waste_cost_by_location(pd.DataFrame(rows))
    locations = set(purchase_by_location) | set(waste)
    out: dict[str, dict[str, float]] = {}
    for loc in locations:
        p = float(purchase_by_location.get(loc, 0.0))
        w = float(waste.get(loc, 0.0))
        out[loc] = {"total_waste_cost": w, "waste_ratio": compute_waste_ratio(p, w)}
    return out


@task(name="compute_stockout_and_price_alert_counts_task")
def compute_stockout_and_price_alert_counts_task(
    rows: list[dict],
) -> dict[str, dict[str, int]]:
    """Transform task: Frecuencia de quiebre de stock + alertas de precio."""
    df = pd.DataFrame(rows)
    stockouts = compute_stockout_events_by_location(df)
    alerts = compute_price_alert_events_by_location(df)
    locations = set(stockouts) | set(alerts)
    return {
        loc: {
            "stockout_events_count": int(stockouts.get(loc, 0)),
            "price_alert_events_count": int(alerts.get(loc, 0)),
        }
        for loc in locations
    }


@task(
    name="assemble_weekly_location_kpi_rows",
    # Cache key = task inputs. Expiration 1h: skip re-assembly when re-triggered soon.
    cache_policy=INPUTS,
    cache_expiration=timedelta(hours=1),
)
def assemble_weekly_location_kpi_rows(extract_result: dict) -> dict:
    """Combine KPI transforms into rows for reporting.weekly_location_performance."""
    week_start = date.fromisoformat(extract_result["week_start"])
    rows = refine_and_aggregate(pd.DataFrame(extract_result.get("rows") or []), week_start)
    return {
        "week_start": week_start.isoformat(),
        "kpi_rows": rows,
        "rows_extracted": int(extract_result.get("rows_extracted") or 0),
    }


@task(
    name="upsert_weekly_location_performance_rows",
    # Retries=3: Load hits Postgres/SQLite; brief locks/timeouts should not fail the week.
    retries=3,
    retry_delay_seconds=5,
)
def upsert_weekly_location_performance_rows(transform_result: dict, run_id: str) -> dict:
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


@task(name="write_weekly_cost_waste_eval_snapshot")
def write_weekly_cost_waste_eval_snapshot(transform_result: dict, load_result: dict) -> str:
    """Optional eval artifact for ops validation under data/eval/."""
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


# ---------------------------------------------------------------------------
# Subflows (≥3) — explicit I/O, no shared globals between stages
# ---------------------------------------------------------------------------


@flow(name="extract_telemetry_events_for_weekly_cost_waste")
def extract_telemetry_events_for_weekly_cost_waste(week_start: date) -> dict:
    """Subflow: extract inbound/waste/stockout/price-alert events for the week."""
    return extract_telemetry_events_for_cost_waste_week(week_start)


@flow(name="transform_weekly_location_cost_waste_kpis")
def transform_weekly_location_cost_waste_kpis(extract_result: dict) -> dict:
    """Subflow: compute CONTEXT KPIs (purchase, waste, ratio, stockouts, price alerts)."""
    rows = extract_result.get("rows") or []
    # Independent transform tasks (unit-testable pieces) run inside the subflow.
    purchase = compute_purchase_cost_by_location_task(rows)
    compute_waste_cost_and_ratio_by_location_task(rows, purchase)
    compute_stockout_and_price_alert_counts_task(rows)
    return assemble_weekly_location_kpi_rows(extract_result)


@flow(name="load_weekly_location_performance_kpis")
def load_weekly_location_performance_kpis(transform_result: dict, run_id: str) -> dict:
    """Subflow: upsert KPI rows into reporting.weekly_location_performance."""
    return upsert_weekly_location_performance_rows(transform_result, run_id)


@flow(name="write_weekly_cost_waste_eval_snapshot_flow")
def write_weekly_cost_waste_eval_snapshot_flow(
    transform_result: dict,
    load_result: dict,
) -> str:
    """Optional subflow: secondary eval export (non-critical)."""
    return write_weekly_cost_waste_eval_snapshot(transform_result, load_result)


# ---------------------------------------------------------------------------
# Main flow — coordinates subflows only
# ---------------------------------------------------------------------------


@flow(name="weekly_location_performance_flow")
def weekly_location_performance_flow(
    week_start: date | None = None,
    triggered_by: str = "scheduler",
) -> dict:
    """Main coordinator: extract → transform → load (+ optional eval subflow)."""
    week_start = week_start or iso_week_start()
    ensure_reporting_tables()
    run_id = open_run(
        pipeline_name=PIPELINE_NAME,
        week_start=week_start,
        triggered_by=triggered_by,
    )
    try:
        extracted = extract_telemetry_events_for_weekly_cost_waste(week_start)
        transformed = transform_weekly_location_cost_waste_kpis(extracted)
        loaded = load_weekly_location_performance_kpis(transformed, run_id)

        # Optional subflow: failure must not abort the main ETL.
        eval_state = write_weekly_cost_waste_eval_snapshot_flow(
            transformed,
            loaded,
            return_state=True,
        )
        eval_ok = eval_state is not None and eval_state.is_completed()
        eval_path = eval_state.result() if eval_ok else None

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
