"""Isolate RAG / MCP / tool text so it is never treated as system instructions."""

from __future__ import annotations

import re
from typing import Any

from agent.guardrails.system_prompt import wrap_untrusted
from agent.guardrails.types import FailureType, GuardDecision, InputClass

# Instruction-like payloads that must be stripped from external content
_INJECTION_IN_DATA = re.compile(
    r"("
    r"ignore\s+(all\s+)?(previous\s+)?instructions|"
    r"ignora(r)?\s+(todas\s+)?(las\s+)?instrucciones|"
    r"system\s*:"
    r"|you\s+are\s+now\s+"
    r"|act\s+as\s+"
    r"|<<<BRASALAND_SYSTEM>>>"
    r"|override\s+guardrails"
    r")",
    re.I,
)


def sanitize_external_text(text: str) -> str:
    """Neutralize instruction-like fragments inside untrusted data."""
    if not text:
        return ""
    cleaned = _INJECTION_IN_DATA.sub("[REDACTED_UNTRUSTED_INSTRUCTION]", text)
    # Collapse obvious role-play markers
    cleaned = re.sub(r"(?im)^\s*(system|assistant)\s*:\s*", "[data] ", cleaned)
    return cleaned


def isolate_rag_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return copies of chunks with sanitized text + provenance tag."""
    out: list[dict[str, Any]] = []
    for c in chunks or []:
        item = dict(c)
        raw = str(item.get("text") or "")
        item["text"] = sanitize_external_text(raw)
        item["untrusted"] = True
        item["authority"] = "data_only"
        out.append(item)
    return out


def isolate_tool_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Mark tool JSON as untrusted data (structural validation)."""
    if payload is None:
        return {"ok": False, "error": "missing_tool_payload", "untrusted": True}
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "error": "malformed_tool_payload",
            "untrusted": True,
            "failure_type": FailureType.STRUCTURAL.value,
        }
    # Shallow sanitize string leaves
    cleaned: dict[str, Any] = {"untrusted": True, "authority": "data_only"}
    for k, v in payload.items():
        if isinstance(v, str):
            cleaned[k] = sanitize_external_text(v)
        else:
            cleaned[k] = v
    return cleaned


def format_untrusted_context(chunks: list[dict[str, Any]]) -> str:
    """Build delimited untrusted context for prompts."""
    parts: list[str] = []
    for c in chunks:
        src = str(c.get("source_document") or c.get("source") or "rag")
        body = str(c.get("text") or "")
        parts.append(wrap_untrusted(body, source=src))
    return "\n".join(parts)


def detect_injection_in_external(text: str) -> GuardDecision | None:
    """If external data itself tries to inject instructions, flag it."""
    if _INJECTION_IN_DATA.search(text or ""):
        return GuardDecision(
            action="block",
            input_class=InputClass.JAILBREAK,
            failure_type=FailureType.SECURITY,
            reason_code="injection_in_external_data",
            message="External data contained instruction-like content; isolated.",
        )
    return None
