"""Persist agent run traces so they remain consultable after execution."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_DIR = _REPO / "data" / "eval" / "agent_traces"


def trace_dir() -> Path:
    override = os.getenv("AGENT_TRACE_DIR", "").strip()
    path = Path(override) if override else DEFAULT_TRACE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def persist_trace(payload: dict[str, Any]) -> Path:
    """Write one JSON trace file per run_id (searchable after the run)."""
    run_id = str(payload.get("run_id") or "unknown")
    record = {
        **payload,
        "persisted_at": datetime.now(timezone.utc).isoformat(),
    }
    path = trace_dir() / f"{run_id}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Also append to an index for listing
    index = trace_dir() / "index.jsonl"
    with index.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "run_id": run_id,
            "nodes": record.get("nodes"),
            "error": record.get("error"),
            "persisted_at": record["persisted_at"],
        }, ensure_ascii=False) + "\n")
    return path


def load_trace(run_id: str) -> dict[str, Any] | None:
    path = trace_dir() / f"{run_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
