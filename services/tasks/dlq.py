"""Dead-letter persistence for Celery tasks that exhaust retries (DEV-55)."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, Session, SQLModel, select

logger = logging.getLogger("celery.brasaland.dlq")

_API_ROOT = Path(__file__).resolve().parents[1] / "api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


class CeleryDeadLetter(SQLModel, table=True):
    """Record of a task moved to the DLQ after max retries."""

    __tablename__ = "celery_dead_letters"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    task_id: str = Field(index=True)
    task_name: str = Field(default="")
    attempt: int = Field(default=0)
    error_message: str = Field(default="")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


def _ensure_table() -> None:
    from app.database import engine

    SQLModel.metadata.create_all(engine, tables=[CeleryDeadLetter.__table__])


def record_dead_letter(
    *,
    task_id: str,
    task_name: str,
    attempt: int,
    error_message: str,
) -> CeleryDeadLetter:
    """Persist DLQ row (task_id, attempt, error, timestamp)."""
    _ensure_table()
    from app.database import engine

    row = CeleryDeadLetter(
        task_id=task_id,
        task_name=task_name,
        attempt=attempt,
        error_message=(error_message or "")[:4000],
    )
    with Session(engine) as session:
        session.add(row)
        session.commit()
        session.refresh(row)
    logger.error(
        "DLQ recorded task_id=%s attempt=%s error=%s",
        task_id,
        attempt,
        error_message,
    )
    return row


def list_dead_letters(limit: int = 50) -> list[CeleryDeadLetter]:
    _ensure_table()
    from app.database import engine

    with Session(engine) as session:
        stmt = (
            select(CeleryDeadLetter)
            .order_by(CeleryDeadLetter.created_at.desc())  # type: ignore[arg-type]
            .limit(limit)
        )
        return list(session.exec(stmt).all())


def get_dead_letter_by_task(task_id: str) -> Optional[CeleryDeadLetter]:
    _ensure_table()
    from app.database import engine

    with Session(engine) as session:
        stmt = select(CeleryDeadLetter).where(CeleryDeadLetter.task_id == task_id)
        return session.exec(stmt).first()
