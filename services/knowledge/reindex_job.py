"""Background reindex job for BrasAI (avoids HTTP 504 on long embed runs)."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_state: dict[str, Any] = {
    "status": "idle",  # idle | running | done | error
    "started_at": None,
    "finished_at": None,
    "result": None,
    "error": None,
}


def get_status() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def _set(**kwargs: Any) -> None:
    with _lock:
        _state.update(kwargs)


def _run(*, recreate: bool) -> None:
    try:
        from data.process.rag import setup as rag_setup

        result = rag_setup(recreate=recreate)
        _set(
            status="done",
            finished_at=datetime.now(timezone.utc).isoformat(),
            result=result,
            error=None,
        )
        logger.info("BrasAI reindex done: %s chunks", result.get("chunks_indexed"))
    except Exception as exc:  # noqa: BLE001
        logger.exception("BrasAI reindex failed")
        _set(
            status="error",
            finished_at=datetime.now(timezone.utc).isoformat(),
            result=None,
            error=str(exc),
        )


def start_reindex(*, recreate: bool = True) -> dict[str, Any]:
    """Start background reindex if idle/done/error. Idempotent while running."""
    with _lock:
        if _state["status"] == "running":
            return dict(_state)
        _state.update(
            {
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
                "result": None,
                "error": None,
            }
        )
    thread = threading.Thread(
        target=_run,
        kwargs={"recreate": recreate},
        name="brasai-reindex",
        daemon=True,
    )
    thread.start()
    return get_status()
