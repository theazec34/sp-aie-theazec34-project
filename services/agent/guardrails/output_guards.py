"""Output validation before the answer reaches the user."""

from __future__ import annotations

import re

from agent.guardrails.system_prompt import (
    REDIRECT_OPS_EN,
    REDIRECT_OPS_ES,
    SENSITIVE_REJECT_ES,
    SYSTEM_BOUNDARY_BEGIN,
)
from agent.guardrails.types import FailureType, OutputCheck
from agent.memory.policy import detect_language

_LEAK_SYSTEM = re.compile(
    r"("
    + re.escape(SYSTEM_BOUNDARY_BEGIN)
    + r"|BRASALAND_SYSTEM|"
    r"ignore your previous instructions|"
    r"my\s+system\s+prompt|"
    r"mis\s+instrucciones\s+ocultas|"
    r"<<<UNTRUSTED_EXTERNAL_DATA"
    r")",
    re.I,
)

_LEAK_SENSITIVE = re.compile(
    r"("
    r"receta\s+madre|"
    r"mother\s+recipe|"
    r"proporci[oó]n\s+exacta|"
    r"\d+\s*(g|kg|ml|l|oz|cups?)\s+(de|of)\s+\w+.{0,40}(salsa|sauce|receta)|"
    r"costo\s+por\s+porci[oó]n\s*[:=]\s*\$?\d|"
    r"cost\s+per\s+portion\s*[:=]\s*\$?\d|"
    r"salario\s+(bruto|neto)|"
    r"payroll\s+amount"
    r")",
    re.I,
)

_MAX_LEN = 8000


def validate_output(answer: str, *, require_redirect: bool = False) -> OutputCheck:
    """Check format, prompt leakage, and sensitive leaks."""
    text = answer if isinstance(answer, str) else str(answer or "")
    lang = detect_language(text)

    if not text.strip():
        return OutputCheck(
            ok=False,
            failure_type=FailureType.STRUCTURAL,
            reason_code="empty_output",
            sanitized_answer=REDIRECT_OPS_EN if lang == "en" else REDIRECT_OPS_ES,
            blocked=True,
        )

    if len(text) > _MAX_LEN:
        return OutputCheck(
            ok=False,
            failure_type=FailureType.STRUCTURAL,
            reason_code="output_too_long",
            sanitized_answer=text[:_MAX_LEN] + "…",
            blocked=False,
        )

    if _LEAK_SYSTEM.search(text):
        return OutputCheck(
            ok=False,
            failure_type=FailureType.SECURITY,
            reason_code="system_prompt_leak",
            sanitized_answer=REDIRECT_OPS_EN if lang == "en" else REDIRECT_OPS_ES,
            blocked=True,
        )

    if _LEAK_SENSITIVE.search(text):
        return OutputCheck(
            ok=False,
            failure_type=FailureType.CONTENT,
            reason_code="sensitive_leak",
            sanitized_answer=SENSITIVE_REJECT_ES if lang != "en" else (
                "I can't share that sensitive information. " + REDIRECT_OPS_EN
            ),
            blocked=True,
        )

    if require_redirect:
        has_ops = bool(
            re.search(
                r"(brasaland|incidencia|inventario|stock|localizaci|location|"
                r"turno|ops|incident)",
                text,
                re.I,
            )
        )
        if not has_ops:
            suffix = REDIRECT_OPS_ES if lang != "en" else REDIRECT_OPS_EN
            return OutputCheck(
                ok=True,
                failure_type=FailureType.CONTENT,
                reason_code="casual_redirect_appended",
                sanitized_answer=text.rstrip() + "\n\n" + suffix,
                blocked=False,
            )

    return OutputCheck(ok=True, sanitized_answer=text, blocked=False)
