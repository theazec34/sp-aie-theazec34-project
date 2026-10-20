"""Registro estructurado de decisiones del agente (NIST Detect / Protect).

Cada turno deja una línea JSONL consultable: intent, guardrails, nodos, tools.
Complementa `tracing.persist_trace` (detalle por run) con un índice de auditoría.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent.decision_log")

_REPO = Path(__file__).resolve().parents[2]
DEFAULT_DIR = _REPO / "data" / "eval" / "agent_decisions"


def decision_dir() -> Path:
    override = os.getenv("AGENT_DECISION_LOG_DIR", "").strip()
    path = Path(override) if override else DEFAULT_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def log_agent_decision(payload: dict[str, Any]) -> Path:
    """Append one audit record; also emit structured logger line."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": payload.get("run_id"),
        "session_id": payload.get("session_id"),
        "user_id": payload.get("user_id"),
        "intent": payload.get("intent"),
        "nodes": list(payload.get("nodes") or []),
        "guard_action": payload.get("guard_action"),
        "guard_reason": payload.get("guard_reason"),
        "guard_failure_type": payload.get("guard_failure_type"),
        "sources_used": list(payload.get("sources_used") or []),
        "memory_decision": payload.get("memory_decision"),
        "checkpointed": bool(payload.get("checkpointed")),
        "error": payload.get("error"),
        # No almacenar la pregunta completa si parece PII — solo longitud
        "question_len": int(payload.get("question_len") or 0),
        "answer_len": len(str(payload.get("answer") or "")),
    }
    path = decision_dir() / "decisions.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    logger.info(
        "agent_decision run_id=%s session_id=%s intent=%s guard=%s nodes=%s",
        record["run_id"],
        record["session_id"],
        record["intent"],
        record["guard_action"] or "none",
        ",".join(record["nodes"][:12]),
    )
    return path


def recent_decisions(limit: int = 50) -> list[dict[str, Any]]:
    path = decision_dir() / "decisions.jsonl"
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
