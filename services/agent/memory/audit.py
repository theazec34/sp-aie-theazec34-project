"""Auditable log of every memory proposal and user decision."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from agent.memory.models import AuditRecord

_LOCK = Lock()


def _audit_path() -> Path:
    raw = os.getenv("AGENT_MEMORY_AUDIT_DIR", "data/eval/agent_memory_audit")
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    path.mkdir(parents=True, exist_ok=True)
    return path / "decisions.jsonl"


def append_audit(record: AuditRecord) -> Path:
    """Append one JSON line — approved and rejected alike (no ghost writes)."""
    target = _audit_path()
    line = record.model_dump_json() + "\n"
    with _LOCK:
        with target.open("a", encoding="utf-8") as fh:
            fh.write(line)
    return target


def read_audit(*, session_id: str | None = None, limit: int = 200) -> list[AuditRecord]:
    target = _audit_path()
    if not target.exists():
        return []
    rows: list[AuditRecord] = []
    with target.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = AuditRecord.model_validate_json(line)
            if session_id and rec.session_id != session_id:
                continue
            rows.append(rec)
    return rows[-limit:]
