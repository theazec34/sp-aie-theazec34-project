"""Task status API — GET /tasks/{task_id} (DEV-55)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

_REPO_SERVICES = Path(__file__).resolve().parents[2]
_API_ROOT = Path(__file__).resolve().parents[1]
for _p in (_REPO_SERVICES, _API_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.auth.deps import get_current_user  # noqa: E402
from app.users.models import UserInDB  # noqa: E402
from celery_app import celery  # noqa: E402
from tasks.dlq import get_dead_letter_by_task, list_dead_letters  # noqa: E402

router = APIRouter(tags=["tasks"])

_STATE_MAP = {
    "PENDING": "pending",
    "RECEIVED": "pending",
    "STARTED": "started",
    "PROGRESS": "started",
    "SUCCESS": "success",
    "FAILURE": "failure",
    "RETRY": "pending",
    "REVOKED": "failure",
}


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str = Field(description="pending | started | success | failure")
    result: Any = None
    error: str | None = None
    dlq: bool = False


class DeadLetterOut(BaseModel):
    id: str
    task_id: str
    task_name: str
    attempt: int
    error_message: str
    created_at: str


def map_celery_status(state: str) -> str:
    return _STATE_MAP.get((state or "").upper(), "pending")


@router.get("/tasks/dlq/recent", response_model=list[DeadLetterOut])
def get_recent_dlq(
    limit: int = 20,
    _user: UserInDB = Depends(get_current_user),
) -> list[DeadLetterOut]:
    """Ops helper: recent dead-letter records (after 3 failed attempts)."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be 1..100")
    rows = list_dead_letters(limit=limit)
    return [
        DeadLetterOut(
            id=r.id,
            task_id=r.task_id,
            task_name=r.task_name,
            attempt=r.attempt,
            error_message=r.error_message,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    _user: UserInDB = Depends(get_current_user),
) -> TaskStatusResponse:
    """Poll Celery result backend (Redis) for task lifecycle status."""
    async_result = AsyncResult(task_id, app=celery)
    state = async_result.state or "PENDING"
    status = map_celery_status(state)
    result: Any = None
    error: str | None = None
    dlq = get_dead_letter_by_task(task_id) is not None

    if status == "success":
        result = async_result.result
    elif status == "failure":
        exc = async_result.result
        error = str(exc) if exc is not None else "task failed"
        if dlq:
            row = get_dead_letter_by_task(task_id)
            if row is not None:
                error = row.error_message

    return TaskStatusResponse(
        task_id=task_id,
        status=status,
        result=result,
        error=error,
        dlq=dlq,
    )
