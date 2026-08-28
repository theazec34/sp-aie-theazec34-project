"""job_runs table helpers: state machine for nightly orchestration.

Postgres uses the public ``job_runs`` table (see sql/job_runs.sql).
SQLite uses the same table name for local fallback (inventory DB).
"""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.database import engine as _default_engine  # noqa: E402

JOB_NAME_NIGHTLY_EXPORT = "nightly_export"
JOB_RUNS_TABLE = "job_runs"


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


def get_engine() -> Engine:
    return _default_engine


def _is_postgres(eng: Engine) -> bool:
    return eng.dialect.name == "postgresql"


def ensure_job_runs_table(eng: Engine | None = None) -> None:
    eng = eng or get_engine()
    with eng.begin() as conn:
        if _is_postgres(eng):
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS job_runs (
                      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                      job_name text NOT NULL,
                      target_date date NOT NULL,
                      status text NOT NULL
                        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
                      started_at timestamptz,
                      finished_at timestamptz,
                      error_message text,
                      created_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_job_runs_job_name_target_date
                      ON job_runs (job_name, target_date)
                    """
                )
            )
        else:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS job_runs (
                      id TEXT PRIMARY KEY,
                      job_name TEXT NOT NULL,
                      target_date TEXT NOT NULL,
                      status TEXT NOT NULL,
                      started_at TEXT,
                      finished_at TEXT,
                      error_message TEXT,
                      created_at TEXT NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS ix_job_runs_job_name_target_date
                      ON job_runs (job_name, target_date)
                    """
                )
            )


def has_processing_lock(job_name: str, *, eng: Engine | None = None) -> bool:
    """True when any run for ``job_name`` is currently ``processing`` (distributed lock)."""
    eng = eng or get_engine()
    ensure_job_runs_table(eng)
    with eng.connect() as conn:
        row = conn.execute(
            text(
                f"""
                SELECT 1 FROM {JOB_RUNS_TABLE}
                WHERE job_name = :job_name AND status = :status
                LIMIT 1
                """
            ),
            {"job_name": job_name, "status": JobStatus.PROCESSING.value},
        ).first()
    return row is not None


def has_completed_for_date(
    job_name: str,
    target_date: date,
    *,
    eng: Engine | None = None,
) -> bool:
    eng = eng or get_engine()
    ensure_job_runs_table(eng)
    td = target_date if _is_postgres(eng) else target_date.isoformat()
    with eng.connect() as conn:
        row = conn.execute(
            text(
                f"""
                SELECT 1 FROM {JOB_RUNS_TABLE}
                WHERE job_name = :job_name
                  AND target_date = :target_date
                  AND status = :status
                LIMIT 1
                """
            ),
            {
                "job_name": job_name,
                "target_date": td,
                "status": JobStatus.COMPLETED.value,
            },
        ).first()
    return row is not None


def create_pending_run(
    job_name: str,
    target_date: date,
    *,
    eng: Engine | None = None,
) -> str:
    eng = eng or get_engine()
    ensure_job_runs_table(eng)
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    td = target_date if _is_postgres(eng) else target_date.isoformat()
    with eng.begin() as conn:
        if _is_postgres(eng):
            conn.execute(
                text(
                    f"""
                    INSERT INTO {JOB_RUNS_TABLE}
                    (id, job_name, target_date, status, created_at)
                    VALUES (:id, :job_name, :target_date, :status, now())
                    """
                ),
                {
                    "id": run_id,
                    "job_name": job_name,
                    "target_date": td,
                    "status": JobStatus.PENDING.value,
                },
            )
        else:
            conn.execute(
                text(
                    f"""
                    INSERT INTO {JOB_RUNS_TABLE}
                    (id, job_name, target_date, status, created_at)
                    VALUES (:id, :job_name, :target_date, :status, :created_at)
                    """
                ),
                {
                    "id": run_id,
                    "job_name": job_name,
                    "target_date": td,
                    "status": JobStatus.PENDING.value,
                    "created_at": now.isoformat(),
                },
            )
    return run_id


def mark_processing(run_id: str, *, eng: Engine | None = None) -> None:
    eng = eng or get_engine()
    with eng.begin() as conn:
        if _is_postgres(eng):
            conn.execute(
                text(
                    f"""
                    UPDATE {JOB_RUNS_TABLE}
                    SET status = :status, started_at = COALESCE(started_at, now())
                    WHERE id = CAST(:run_id AS uuid)
                    """
                ),
                {"run_id": run_id, "status": JobStatus.PROCESSING.value},
            )
        else:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                text(
                    f"""
                    UPDATE {JOB_RUNS_TABLE}
                    SET status = :status, started_at = COALESCE(started_at, :started_at)
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "status": JobStatus.PROCESSING.value,
                    "started_at": now,
                },
            )


def mark_completed(run_id: str, *, eng: Engine | None = None) -> None:
    _finish_run(run_id, JobStatus.COMPLETED.value, error_message=None, eng=eng)


def mark_failed(
    run_id: str,
    error_message: str,
    *,
    eng: Engine | None = None,
) -> None:
    _finish_run(run_id, JobStatus.FAILED.value, error_message=error_message[:500], eng=eng)


def _finish_run(
    run_id: str,
    status: str,
    *,
    error_message: str | None,
    eng: Engine | None = None,
) -> None:
    eng = eng or get_engine()
    with eng.begin() as conn:
        if _is_postgres(eng):
            conn.execute(
                text(
                    f"""
                    UPDATE {JOB_RUNS_TABLE}
                    SET status = :status,
                        finished_at = now(),
                        error_message = :error_message
                    WHERE id = CAST(:run_id AS uuid)
                    """
                ),
                {"run_id": run_id, "status": status, "error_message": error_message},
            )
        else:
            conn.execute(
                text(
                    f"""
                    UPDATE {JOB_RUNS_TABLE}
                    SET status = :status,
                        finished_at = :finished_at,
                        error_message = :error_message
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "status": status,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": error_message,
                },
            )


def get_run(run_id: str, *, eng: Engine | None = None) -> dict[str, Any] | None:
    eng = eng or get_engine()
    ensure_job_runs_table(eng)
    with eng.connect() as conn:
        if _is_postgres(eng):
            row = conn.execute(
                text(
                    f"""
                    SELECT id, job_name, target_date, status, started_at, finished_at,
                           error_message, created_at
                    FROM {JOB_RUNS_TABLE}
                    WHERE id = CAST(:run_id AS uuid)
                    """
                ),
                {"run_id": run_id},
            ).mappings().first()
        else:
            row = conn.execute(
                text(
                    f"""
                    SELECT id, job_name, target_date, status, started_at, finished_at,
                           error_message, created_at
                    FROM {JOB_RUNS_TABLE}
                    WHERE id = :run_id
                    """
                ),
                {"run_id": run_id},
            ).mappings().first()
    if not row:
        return None
    return {k: (str(v) if v is not None else None) for k, v in row.items()}
