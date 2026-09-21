"""Celery application — Redis broker + result backend (DEV-55).

Run worker (repo root, PYTHONPATH includes ``services/``):

    celery -A celery_app.celery worker --loglevel=INFO

Flower:

    celery -A celery_app.celery flower --port=5555
"""

from __future__ import annotations

import os
from pathlib import Path

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun
from dotenv import load_dotenv

# Load monorepo .env when present
for root in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
    candidate = root / ".env"
    if candidate.exists():
        load_dotenv(candidate)
        break

REDIS_URL = (os.getenv("REDIS_URL") or "redis://127.0.0.1:6379/0").strip()

celery = Celery(
    "brasaland",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.incidents"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=86400,
    # Soft/hard limits prevent hung workers from blocking the pool
    task_soft_time_limit=int(os.getenv("CELERY_SOFT_TIME_LIMIT", "120")),
    task_time_limit=int(os.getenv("CELERY_TIME_LIMIT", "180")),
)


@task_prerun.connect
def _log_prerun(task_id=None, task=None, **_kwargs):
    import logging
    import time

    logging.getLogger("celery.brasaland").info(
        "task_start task_id=%s name=%s attempt=%s",
        task_id,
        getattr(task, "name", "?"),
        (getattr(getattr(task, "request", None), "retries", 0) or 0) + 1,
    )
    # stash start time on request
    if task is not None and getattr(task, "request", None) is not None:
        task.request._brasaland_t0 = time.perf_counter()


@task_postrun.connect
def _log_postrun(task_id=None, task=None, state=None, **_kwargs):
    import logging
    import time

    t0 = getattr(getattr(task, "request", None), "_brasaland_t0", None)
    duration_ms = (time.perf_counter() - t0) * 1000 if t0 else -1
    logging.getLogger("celery.brasaland").info(
        "task_end task_id=%s name=%s status=%s attempt=%s duration_ms=%.1f",
        task_id,
        getattr(task, "name", "?"),
        state,
        (getattr(getattr(task, "request", None), "retries", 0) or 0) + 1,
        duration_ms,
    )


@task_failure.connect
def _log_failure(task_id=None, exception=None, sender=None, einfo=None, **_kwargs):
    import logging

    retries = 0
    if sender is not None and getattr(sender, "request", None) is not None:
        retries = getattr(sender.request, "retries", 0) or 0
    logging.getLogger("celery.brasaland").error(
        "task_failure task_id=%s attempt=%s error=%s",
        task_id,
        retries + 1,
        exception,
    )
