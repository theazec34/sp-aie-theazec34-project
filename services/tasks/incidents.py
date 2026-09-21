"""Heavy incident CSV analysis as a Celery task (DEV-55).

Messages carry only ``upload_id`` + filename — the worker reads the file
from disk (no large payloads on the broker).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

from celery_app import celery
from tasks.dlq import record_dead_letter

logger = logging.getLogger("celery.brasaland.incidents")

_API_ROOT = Path(__file__).resolve().parents[1] / "api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

UPLOAD_DIR = _API_ROOT / "data" / "uploads"


def upload_path(upload_id: str) -> Path:
    return UPLOAD_DIR / f"{upload_id}.csv"


@celery.task(
    bind=True,
    name="tasks.incidents.analyze_incidents_csv",
    max_retries=3,
    acks_late=True,
)
def analyze_incidents_csv(
    self,
    upload_id: str,
    original_filename: str,
    *,
    force_fail: bool = False,
) -> dict:
    """Analyze a previously uploaded CSV; retry with exponential backoff."""
    attempt = (self.request.retries or 0) + 1
    task_id = self.request.id or ""
    path = upload_path(upload_id)

    try:
        if force_fail:
            raise RuntimeError("Forced failure for DLQ / retry demonstration")

        if not path.is_file():
            raise FileNotFoundError(f"Upload not found: {upload_id}")

        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise ValueError("El fichero CSV está vacío.")

        from app.analyzer import analyze_text, build_report

        result = analyze_text(content, original_filename or path.name)
        report = build_report(result)
        logger.info(
            "analyze_ok task_id=%s attempt=%s upload_id=%s records=%s",
            task_id,
            attempt,
            upload_id,
            report.get("total_records"),
        )
        return report

    except SoftTimeLimitExceeded:
        error = "soft time limit exceeded"
        _maybe_dlq_and_retry(self, task_id, attempt, error)
        raise
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
        _maybe_dlq_and_retry(self, task_id, attempt, error, exc)
        raise


def _maybe_dlq_and_retry(self, task_id: str, attempt: int, error: str, exc: BaseException | None = None) -> None:
    """Exponential backoff retry; after max_retries persist DLQ and stop."""
    max_retries = int(getattr(self, "max_retries", 3) or 3)
    if self.request.retries >= max_retries:
        record_dead_letter(
            task_id=task_id,
            task_name=self.name,
            attempt=attempt,
            error_message=error,
        )
        logger.error(
            "analyze_dlq task_id=%s attempt=%s error=%s",
            task_id,
            attempt,
            error,
        )
        return

    countdown = 2 ** (self.request.retries + 1)  # 2, 4, 8 seconds
    logger.warning(
        "analyze_retry task_id=%s attempt=%s countdown=%ss error=%s",
        task_id,
        attempt,
        countdown,
        error,
    )
    try:
        raise self.retry(exc=exc or RuntimeError(error), countdown=countdown)
    except MaxRetriesExceededError:
        record_dead_letter(
            task_id=task_id,
            task_name=self.name,
            attempt=attempt,
            error_message=error,
        )
