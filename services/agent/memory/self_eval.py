"""Self-evaluation after each relevant turn — structured output, single pass.

Produces ``propuesta_memoria`` or discards. Never writes memory here.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from agent.memory.models import MemoryCategory, MemoryProposal, SelfEvalResult
from agent.memory.policy import (
    detect_category,
    detect_language,
    extract_location,
    forbidden_reason,
    is_correction_signal,
    non_memorable_reason,
)


def _normalize_fact(text: str, category: MemoryCategory, location: str | None) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    # Prefer a concise operational statement
    if len(cleaned) > 280:
        cleaned = cleaned[:277] + "..."
    prefix = []
    if location:
        prefix.append(location)
    prefix.append(category.value)
    return f"{'/'.join(prefix)}: {cleaned}"


def evaluate_for_memory(
    user_message: str,
    agent_answer: str = "",
    *,
    language_hint: str | None = None,
) -> SelfEvalResult:
    """
    Structured self-eval (deterministic rules aligned with CONTEXT).

    When ``AGENT_MEMORY_LLM=1`` and ``OPENAI_API_KEY`` is set, optionally
    refine with a single structured model call; otherwise rules alone decide.
    """
    text = (user_message or "").strip()
    if not text:
        return SelfEvalResult(memorable=False, discard_reason="empty_message")

    ban = forbidden_reason(text)
    if ban:
        return SelfEvalResult(memorable=False, discard_reason=f"forbidden:{ban}")

    skip = non_memorable_reason(text)
    if skip and not is_correction_signal(text):
        return SelfEvalResult(memorable=False, discard_reason=f"non_memorable:{skip}")

    category = detect_category(text)
    if category is None and not is_correction_signal(text):
        return SelfEvalResult(memorable=False, discard_reason="no_operational_signal")

    if category is None:
        category = MemoryCategory.OTHER_OPERATIONAL

    # Require correction / lasting operational signal — not every supplier mention
    if category == MemoryCategory.OTHER_OPERATIONAL and not is_correction_signal(text):
        return SelfEvalResult(memorable=False, discard_reason="weak_signal")

    location = extract_location(text)
    lang = language_hint or detect_language(text)
    fact = _normalize_fact(text, category, location)
    reason = _reason_for(category, lang)

    proposal = MemoryProposal(
        fact=fact,
        reason=reason,
        location=location,
        category=category,
        language=lang if lang in ("es", "en") else "es",  # type: ignore[arg-type]
        source_message=text,
    )

    if os.getenv("AGENT_MEMORY_LLM", "0") == "1":
        refined = _llm_refine(text, agent_answer, proposal)
        if refined is not None:
            return refined

    return SelfEvalResult(memorable=True, propuesta_memoria=proposal)


def _reason_for(category: MemoryCategory, lang: str) -> str:
    reasons_es = {
        MemoryCategory.HOURS: "Corrección de horario operativo por location (reutilizable).",
        MemoryCategory.SUPPLIER: "Corrección de día/proveedor recurrente por location.",
        MemoryCategory.INCIDENT_PATTERN: "Patrón de escalación conocida (evitar re-escalar).",
        MemoryCategory.COMM_PREFERENCE: "Preferencia de comunicación de un gerente de local.",
        MemoryCategory.OTHER_OPERATIONAL: "Corrección operativa con patrón repetible.",
    }
    reasons_en = {
        MemoryCategory.HOURS: "Recurring location hours correction.",
        MemoryCategory.SUPPLIER: "Recurring supplier delivery-day correction.",
        MemoryCategory.INCIDENT_PATTERN: "Known escalation pattern (avoid re-escalating).",
        MemoryCategory.COMM_PREFERENCE: "Manager communication preference.",
        MemoryCategory.OTHER_OPERATIONAL: "Repeatable operational correction.",
    }
    table = reasons_en if lang == "en" else reasons_es
    return table[category]


def _llm_refine(
    user_message: str,
    agent_answer: str,
    fallback: MemoryProposal,
) -> SelfEvalResult | None:
    """Optional single structured call — never a multi-agent loop."""
    try:
        from openai import OpenAI
    except ImportError:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None

    client = OpenAI()
    schema_hint = {
        "memorable": "bool",
        "propuesta_memoria": {
            "fact": "str",
            "reason": "str",
            "location": "str|null",
            "category": "hours|supplier|incident_pattern|comm_preference|other_operational",
            "language": "es|en",
        },
        "discard_reason": "str|null",
    }
    prompt = (
        "You are the Brasaland manager-support agent self-evaluator. "
        "Return ONLY JSON matching this schema: "
        f"{json.dumps(schema_hint)}. "
        "Memorable = recurring operational corrections (hours, suppliers, known "
        "incident patterns, manager preferences). NEVER memorize customer PII, "
        "payroll, or one-off queries. If not memorable, memorable=false.\n\n"
        f"USER: {user_message}\nAGENT: {agent_answer}\n"
    )
    try:
        resp = client.chat.completions.create(
            model=os.getenv("AGENT_MEMORY_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        data: dict[str, Any] = json.loads(raw)
    except Exception:  # noqa: BLE001
        return None

    if not data.get("memorable"):
        return SelfEvalResult(
            memorable=False,
            discard_reason=str(data.get("discard_reason") or "llm_discard"),
        )
    prop = data.get("propuesta_memoria") or {}
    try:
        proposal = MemoryProposal(
            fact=str(prop.get("fact") or fallback.fact),
            reason=str(prop.get("reason") or fallback.reason),
            location=prop.get("location") or fallback.location,
            category=MemoryCategory(prop.get("category") or fallback.category.value),
            language=prop.get("language") or fallback.language,
            source_message=user_message,
        )
    except Exception:  # noqa: BLE001
        return SelfEvalResult(memorable=True, propuesta_memoria=fallback)
    return SelfEvalResult(memorable=True, propuesta_memoria=proposal)


def format_proposal_question(proposal: MemoryProposal) -> str:
    """Append bilingual confirmation ask — never write yet."""
    if proposal.language == "en":
        return (
            f"\n\n—\nI can remember this for next time: «{proposal.fact}». "
            "Do you want me to save it? (yes / no / edit: <corrected text>)"
        )
    return (
        f"\n\n—\n¿Quieres que recuerde esto para la próxima vez?: «{proposal.fact}». "
        "(sí / no / editar: <texto corregido>)"
    )
