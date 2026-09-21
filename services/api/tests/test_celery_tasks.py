"""DEV-55 — Celery async analyze + task status + DLQ."""

from __future__ import annotations

import io
import time

import pytest
from fastapi.testclient import TestClient


CSV_MINIMAL = (
    "incident_id,location_id,category,description,status,reporter_id,score\n"
    "1,bogota,food,ok,closed,u1,5\n"
)


def test_map_celery_status():
    from app.tasks_router import map_celery_status

    assert map_celery_status("PENDING") == "pending"
    assert map_celery_status("STARTED") == "started"
    assert map_celery_status("SUCCESS") == "success"
    assert map_celery_status("FAILURE") == "failure"


def test_analyze_returns_202_with_task_id_quickly(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    class _FakeAsync:
        id = "fake-task-id-123"

    def _fake_delay(*_a, **_k):
        return _FakeAsync()

    import tasks.incidents as incidents_tasks

    monkeypatch.setattr(incidents_tasks.analyze_incidents_csv, "delay", _fake_delay)

    t0 = time.perf_counter()
    response = client.post(
        "/api/v1/incidents/analyze",
        headers=auth_header,
        files={"file": ("sample.csv", io.BytesIO(CSV_MINIMAL.encode()), "text/csv")},
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["task_id"] == "fake-task-id-123"
    assert elapsed_ms < 200, f"enqueue took {elapsed_ms:.1f}ms (>200ms)"


def test_get_task_status_success(
    client: TestClient,
    auth_header: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
):
    class _Result:
        state = "SUCCESS"
        result = {"total_records": 1, "source_file": "sample.csv"}

    monkeypatch.setattr(
        "app.tasks_router.AsyncResult",
        lambda *_a, **_k: _Result(),
    )
    monkeypatch.setattr("app.tasks_router.get_dead_letter_by_task", lambda _tid: None)

    response = client.get("/tasks/any-id", headers=auth_header)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["result"]["total_records"] == 1
    assert payload["dlq"] is False


def test_dlq_record_persists():
    from tasks.dlq import get_dead_letter_by_task, record_dead_letter

    row = record_dead_letter(
        task_id="dlq-task-1",
        task_name="tasks.incidents.analyze_incidents_csv",
        attempt=4,
        error_message="Forced failure",
    )
    assert row.task_id == "dlq-task-1"
    assert row.attempt == 4
    found = get_dead_letter_by_task("dlq-task-1")
    assert found is not None
    assert "Forced" in found.error_message


def test_analyze_task_success_eager():
    """Run task body synchronously (no broker) for unit coverage."""
    from tasks.incidents import UPLOAD_DIR, analyze_incidents_csv, upload_path

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    upload_id = "unit-upload-ok"
    path = upload_path(upload_id)
    path.write_text(CSV_MINIMAL, encoding="utf-8")

    result = analyze_incidents_csv.run(upload_id, "sample.csv", force_fail=False)
    assert result["total_records"] >= 1
    path.unlink(missing_ok=True)
