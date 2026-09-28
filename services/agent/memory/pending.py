"""At most one pending memory proposal per session."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from agent.memory.models import PendingProposal

_LOCK = Lock()


def _path() -> Path:
    raw = os.getenv("AGENT_MEMORY_DIR", "data/eval/agent_memory")
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    path.mkdir(parents=True, exist_ok=True)
    return path / "pending.json"


def get_pending(session_id: str) -> PendingProposal | None:
    with _LOCK:
        data = _load()
        raw = data.get(session_id)
        if not raw:
            return None
        return PendingProposal.model_validate(raw)


def set_pending(pending: PendingProposal) -> None:
    """Replace any existing pending for this session (max one)."""
    with _LOCK:
        data = _load()
        data[pending.session_id] = pending.model_dump(mode="json")
        _save(data)


def clear_pending(session_id: str) -> None:
    with _LOCK:
        data = _load()
        if session_id in data:
            del data[session_id]
            _save(data)


def _load() -> dict:
    p = _path()
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    _path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
