"""Harness facade — orchestrates input/output/isolation guardrails."""

from __future__ import annotations

from typing import Any

from agent.guardrails.input_guards import classify_input
from agent.guardrails.isolation import (
    detect_injection_in_external,
    format_untrusted_context,
    isolate_rag_chunks,
    isolate_tool_payload,
    sanitize_external_text,
)
from agent.guardrails.observability import record_guard_event
from agent.guardrails.output_guards import validate_output
from agent.guardrails.system_prompt import SECURE_SYSTEM_PROMPT, build_generation_messages
from agent.guardrails.types import GuardDecision, OutputCheck


def guard_user_input(question: str, *, session_id: str = "default") -> GuardDecision:
    decision = classify_input(question, session_id=session_id)
    if decision.action != "allow":
        record_guard_event(
            stage="input",
            decision=decision,
            session_id=session_id,
            question=question,
        )
    return decision


def guard_answer(
    answer: str,
    *,
    session_id: str | None = None,
    require_redirect: bool = False,
    question: str | None = None,
) -> OutputCheck:
    check = validate_output(answer, require_redirect=require_redirect)
    if check.blocked or not check.ok or check.reason_code == "casual_redirect_appended":
        record_guard_event(
            stage="output",
            output=check,
            session_id=session_id,
            question=question,
        )
    return check


def prepare_rag_context(chunks: list[dict[str, Any]], *, session_id: str | None = None) -> list[dict[str, Any]]:
    isolated = isolate_rag_chunks(chunks)
    for c in isolated:
        inj = detect_injection_in_external(str(c.get("text") or ""))
        if inj is not None:
            record_guard_event(stage="rag_isolation", decision=inj, session_id=session_id)
            c["text"] = sanitize_external_text(str(c.get("text") or ""))
    return isolated


def prepare_tool_result(
    payload: dict[str, Any] | None, *, session_id: str | None = None
) -> dict[str, Any]:
    cleaned = isolate_tool_payload(payload)
    if cleaned.get("failure_type") == "structural":
        from agent.guardrails.types import FailureType, InputClass

        decision = GuardDecision(
            action="block",
            input_class=InputClass.DOMAIN,
            failure_type=FailureType.STRUCTURAL,
            reason_code="malformed_tool_payload",
            message="Tool payload malformed",
        )
        record_guard_event(stage="tool_isolation", decision=decision, session_id=session_id)
    return cleaned


__all__ = [
    "SECURE_SYSTEM_PROMPT",
    "build_generation_messages",
    "format_untrusted_context",
    "guard_answer",
    "guard_user_input",
    "prepare_rag_context",
    "prepare_tool_result",
]
