#!/usr/bin/env python3
"""Nightly telemetry export + pipeline trigger (independent worker process).

Exports ``telemetry_events`` for ``target_date`` to ``data/raw/telemetry_YYYY-MM-DD.csv``
(backup/audit only — the business pipeline reads from the DB, not this CSV).

State machine in ``job_runs``: pending → processing → completed | failed.

Usage:
    python scripts/nightly_export.py
    TARGET_DATE=2026-01-15 python scripts/nightly_export.py
"""

from __future__ import annotations

import csv
import json
import logging
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text

_REPO_ROOT = Path(__file__).resolve().parents[1]
_API_ROOT = _REPO_ROOT / "services" / "api"
_SERVICES_ROOT = _REPO_ROOT / "services"
_RAW_DIR = _REPO_ROOT / "data" / "raw"

for _p in (_REPO_ROOT, _API_ROOT, _SERVICES_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.database import engine  # noqa: E402
from job_runner import (  # noqa: E402
    JOB_NAME_NIGHTLY_EXPORT,
    JobStatus,
    create_pending_run,
    has_completed_for_date,
    has_processing_lock,
    mark_completed,
    mark_failed,
    mark_processing,
)

JOB_NAME = JOB_NAME_NIGHTLY_EXPORT
logger = logging.getLogger("nightly_export")


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


def _log(level: int, state: str, message: str, *args: object) -> None:
    logger.log(level, "job=%s state=%s " + message, JOB_NAME, state, *args)


def resolve_target_date() -> date:
    override = (os.getenv("TARGET_DATE") or "").strip()
    if override:
        return date.fromisoformat(override)
    return datetime.now(timezone.utc).date() - timedelta(days=1)


def _day_window(target_date: date) -> tuple[datetime, datetime]:
    start = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        tzinfo=timezone.utc,
    )
    return start, start + timedelta(days=1)


def csv_path_for(target_date: date) -> Path:
    return _RAW_DIR / f"telemetry_{target_date.isoformat()}.csv"


def export_telemetry_csv(target_date: date) -> Path:
    """Write CSV backup if missing; idempotent per file path."""
    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = csv_path_for(target_date)
    if out_path.exists():
        _log(logging.INFO, JobStatus.PROCESSING.value, "csv_exists path=%s", out_path)
        return out_path

    day_start, day_end = _day_window(target_date)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT event_id, event_type, timestamp, service, session_id, user_id, tags
                FROM telemetry_events
                WHERE timestamp >= :day_start AND timestamp < :day_end
                ORDER BY timestamp, event_id
                """
            ),
            {"day_start": day_start, "day_end": day_end},
        ).mappings().all()

    fieldnames = [
        "event_id",
        "event_type",
        "timestamp",
        "service",
        "session_id",
        "user_id",
        "tags",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            tags = row["tags"]
            if isinstance(tags, str):
                tags_str = tags
            else:
                tags_str = json.dumps(tags or {}, ensure_ascii=False)
            writer.writerow(
                {
                    "event_id": row["event_id"],
                    "event_type": row["event_type"],
                    "timestamp": str(row["timestamp"]),
                    "service": row["service"],
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "tags": tags_str,
                }
            )

    _log(
        logging.INFO,
        JobStatus.PROCESSING.value,
        "csv_exported path=%s rows=%d",
        out_path,
        len(rows),
    )
    return out_path


def week_start_for(target_date: date) -> date:
    return target_date - timedelta(days=target_date.weekday())


def run_pipeline_subprocess(target_date: date) -> None:
    week_start = week_start_for(target_date)
    pipeline_script = _REPO_ROOT / "data" / "pipelines" / "pipeline.py"
    cmd = [
        sys.executable,
        str(pipeline_script),
        "--week-start",
        week_start.isoformat(),
        "--triggered-by",
        JOB_NAME,
    ]
    _log(
        logging.INFO,
        JobStatus.PROCESSING.value,
        "pipeline_start week_start=%s cmd=%s",
        week_start.isoformat(),
        " ".join(cmd),
    )
    result = subprocess.run(
        cmd,
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "pipeline subprocess failed").strip()
        raise RuntimeError(detail[:500])
    _log(logging.INFO, JobStatus.PROCESSING.value, "pipeline_finished week_start=%s", week_start.isoformat())


def run() -> int:
    target_date = resolve_target_date()
    _log(logging.INFO, "init", "target_date=%s", target_date.isoformat())

    if has_processing_lock(JOB_NAME):
        _log(logging.INFO, JobStatus.PROCESSING.value, "aborted lock_held")
        return 0

    if has_completed_for_date(JOB_NAME, target_date):
        _log(logging.INFO, JobStatus.COMPLETED.value, "skipped already_completed target_date=%s", target_date.isoformat())
        return 0

    run_id = create_pending_run(JOB_NAME, target_date)
    _log(logging.INFO, JobStatus.PENDING.value, "run_created run_id=%s", run_id)

    mark_processing(run_id)
    _log(logging.INFO, JobStatus.PROCESSING.value, "run_started run_id=%s", run_id)

    try:
        export_telemetry_csv(target_date)
        run_pipeline_subprocess(target_date)
        mark_completed(run_id)
        _log(logging.INFO, JobStatus.COMPLETED.value, "run_finished run_id=%s", run_id)
        return 0
    except Exception as exc:  # noqa: BLE001
        mark_failed(run_id, str(exc))
        _log(logging.ERROR, JobStatus.FAILED.value, "run_failed run_id=%s error=%s", run_id, exc)
        return 1


def main() -> int:
    _configure_logging()
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
