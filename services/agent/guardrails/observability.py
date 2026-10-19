"""Guardrail observability — log every block/redirect + session summary."""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.guardrails.types import FailureType, GuardDecision, OutputCheck

logger = logging.getLogger("agent.guardrails")

_LOCK = threading.Lock()
_COUNTERS: Counter[str] = Counter()
_EVENTS: list[dict[str, Any]] = []


def _log_path() -> Path:
    raw = os.getenv("AGENT_GUARDRAIL_LOG_DIR", "data/eval/agent_guardrails")
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    path.mkdir(parents=True, exist_ok=True)
    return path / "events.jsonl"


def record_guard_event(
    *,
    stage: str,
    decision: GuardDecision | None = None,
    output: OutputCheck | None = None,
    session_id: str | None = None,
    question: str | None = None,
) -> None:
    """Log a block or redirect with failure type (structural|content|security)."""
    failure: str | None = None
    action = "allow"
    reason = "ok"
    if decision is not None:
        action = decision.action
        reason = decision.reason_code
        failure = decision.failure_type.value if decision.failure_type else None
    if output is not None and (output.blocked or not output.ok):
        action = "block" if output.blocked else "sanitize"
        reason = output.reason_code or "output_check"
        failure = output.failure_type.value if output.failure_type else FailureType.CONTENT.value

    if action == "allow":
        return

    key = f"{stage}:{action}:{failure or 'none'}:{reason}"
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "action": action,
        "failure_type": failure,
        "reason_code": reason,
        "session_id": session_id,
        "question_preview": (question or "")[:160],
    }
    with _LOCK:
        _COUNTERS[key] += 1
        _COUNTERS[f"failure:{failure or 'none'}"] += 1
        _COUNTERS[f"action:{action}"] += 1
        _EVENTS.append(event)
        if len(_EVENTS) > 2000:
            del _EVENTS[:1000]
        with _log_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    logger.warning(
        "guardrail_%s failure_type=%s reason=%s session=%s",
        action,
        failure,
        reason,
        session_id,
    )


def guardrail_summary() -> dict[str, Any]:
    """Summary of how many times each guardrail fired in this process/session."""
    with _LOCK:
        by_failure = {
            "structural": _COUNTERS.get("failure:structural", 0),
            "content": _COUNTERS.get("failure:content", 0),
            "security": _COUNTERS.get("failure:security", 0),
        }
        by_action = {
            "block": _COUNTERS.get("action:block", 0),
            "redirect": _COUNTERS.get("action:redirect", 0),
            "sanitize": _COUNTERS.get("action:sanitize", 0),
        }
        detail = {
            k: v
            for k, v in _COUNTERS.items()
            if not k.startswith("failure:") and not k.startswith("action:")
        }
        recent = list(_EVENTS[-50:])
    return {
        "by_failure_type": by_failure,
        "by_action": by_action,
        "detail": detail,
        "recent_events": recent,
        "total_activations": sum(by_action.values()),
    }


def reset_guardrail_stats_for_tests() -> None:
    with _LOCK:
        _COUNTERS.clear()
        _EVENTS.clear()
