"""Tests for nightly export orchestration (job_runs + scripts/nightly_export)."""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlmodel import Session

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
_SERVICES_ROOT = _REPO_ROOT / "services"
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
for _p in (_REPO_ROOT, _API_ROOT, _SERVICES_ROOT, _SCRIPTS_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.database import engine, init_db  # noqa: E402
from app.telemetry import orm as _telemetry_orm  # noqa: F401, E402
from app.telemetry.models import TelemetryEvent  # noqa: E402
from app.telemetry.repository import bulk_insert_events  # noqa: E402
from job_runner.db import (  # noqa: E402
    JOB_NAME_NIGHTLY_EXPORT,
    JobStatus,
    create_pending_run,
    ensure_job_runs_table,
    get_run,
    has_completed_for_date,
    has_processing_lock,
    mark_completed,
    mark_failed,
    mark_processing,
)
import nightly_export  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_job_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ensure_job_runs_table(engine)
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM job_runs"))
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    monkeypatch.setattr(nightly_export, "_RAW_DIR", raw_dir)
    yield


def _seed_event_for_day(target: date) -> None:
    init_db()
    when = datetime(target.year, target.month, target.day, 12, tzinfo=timezone.utc)
    event = TelemetryEvent(
        eventId=str(uuid.uuid4()),
        timestamp=when.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        sessionId=str(uuid.uuid4()),
        userId="1",
        event_type="page_viewed",
        schemaVersion="1.0.0",
        requestId=str(uuid.uuid4()),
        properties={"route": "/inventory"},
    )
    with Session(engine) as session:
        bulk_insert_events(session, [event])


def test_has_processing_lock_detects_active_run() -> None:
    target = date(2026, 1, 15)
    run_id = create_pending_run(JOB_NAME_NIGHTLY_EXPORT, target)
    mark_processing(run_id)
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is True


def test_has_completed_for_date() -> None:
    target = date(2026, 1, 16)
    run_id = create_pending_run(JOB_NAME_NIGHTLY_EXPORT, target)
    mark_processing(run_id)
    mark_completed(run_id)
    assert has_completed_for_date(JOB_NAME_NIGHTLY_EXPORT, target) is True


def test_failed_run_never_stays_processing() -> None:
    target = date(2026, 1, 17)
    run_id = create_pending_run(JOB_NAME_NIGHTLY_EXPORT, target)
    mark_processing(run_id)
    mark_failed(run_id, "boom")
    row = get_run(run_id)
    assert row is not None
    assert row["status"] == JobStatus.FAILED.value
    assert row["error_message"] == "boom"
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is False


def test_nightly_export_skips_when_completed(monkeypatch: pytest.MonkeyPatch) -> None:
    target = date(2026, 1, 18)
    run_id = create_pending_run(JOB_NAME_NIGHTLY_EXPORT, target)
    mark_processing(run_id)
    mark_completed(run_id)

    monkeypatch.setattr(nightly_export, "resolve_target_date", lambda: target)
    called = {"pipeline": False}
    monkeypatch.setattr(
        nightly_export,
        "run_pipeline_subprocess",
        lambda _d: called.__setitem__("pipeline", True),
    )
    assert nightly_export.run() == 0
    assert called["pipeline"] is False


def test_nightly_export_aborts_on_processing_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    target = date(2026, 1, 19)
    other = create_pending_run(JOB_NAME_NIGHTLY_EXPORT, target)
    mark_processing(other)

    monkeypatch.setattr(nightly_export, "resolve_target_date", lambda: target + timedelta(days=1))
    called = {"pipeline": False}
    monkeypatch.setattr(
        nightly_export,
        "run_pipeline_subprocess",
        lambda _d: called.__setitem__("pipeline", True),
    )
    assert nightly_export.run() == 0
    assert called["pipeline"] is False


def test_export_telemetry_csv_creates_file() -> None:
    target = date(2026, 1, 20)
    _seed_event_for_day(target)
    path = nightly_export.export_telemetry_csv(target)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "event_id,event_type,timestamp" in text
    assert "page_viewed" in text


def test_nightly_export_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    target = date(2026, 1, 21)
    _seed_event_for_day(target)
    monkeypatch.setattr(nightly_export, "resolve_target_date", lambda: target)
    monkeypatch.setattr(nightly_export, "run_pipeline_subprocess", lambda _d: None)

    assert nightly_export.run() == 0
    assert has_completed_for_date(JOB_NAME_NIGHTLY_EXPORT, target) is True
    assert nightly_export.csv_path_for(target).exists()


def test_nightly_export_marks_failed_on_pipeline_error(monkeypatch: pytest.MonkeyPatch) -> None:
    target = date(2026, 1, 22)
    _seed_event_for_day(target)
    monkeypatch.setattr(nightly_export, "resolve_target_date", lambda: target)

    def _boom(_d: date) -> None:
        raise RuntimeError("pipeline down")

    monkeypatch.setattr(nightly_export, "run_pipeline_subprocess", _boom)
    assert nightly_export.run() == 1
    assert has_processing_lock(JOB_NAME_NIGHTLY_EXPORT) is False
    assert has_completed_for_date(JOB_NAME_NIGHTLY_EXPORT, target) is False
