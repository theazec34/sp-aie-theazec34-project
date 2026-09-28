"""Explicit confirmation intent classification (labels, not naive 'yes' search)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from agent.memory.models import ConfirmLabel


@dataclass(frozen=True)
class ConfirmResult:
    label: ConfirmLabel
    edited_fact: str | None = None
    confidence: float = 1.0


# Ordered rules — first match wins. Bilingual ES/EN.
_APPROVE = re.compile(
    r"^\s*("
    r"s[ií]|yes|yep|yeah|ok(ay)?|vale|de acuerdo|correcto|confirma(r|do)?|"
    r"guarda(r|lo|la)?|recu[eé]rda(lo)?|save\s*it|please\s*save|afirmativo|"
    r"dale|perfecto\s*,?\s*gu[aá]rdalo"
    r")\b",
    re.I,
)
_REJECT = re.compile(
    r"^\s*("
    r"no|nop|nope|nah|cancel(a|ar)?|descarta(r)?|olvid(a|ar)|don'?t\s*save|"
    r"do\s*not\s*save|rechaz(a|ar)|nunca|never"
    r")\b",
    re.I,
)
_EDIT = re.compile(
    r"^\s*(?:"
    r"editar|edit|corrige|corregir|change\s*to|cambi(?:a|ar)\s*a"
    r")\s*:?\s*(.+)$",
    re.I | re.S,
)
# Soft approve only when short + clear affirmative (avoid matching inside long sentences)
_SOFT_APPROVE = re.compile(
    r"^\s*(s[ií]|yes|yep|ok|vale|de acuerdo|guarda(r)?|save)[!?.\s]*$",
    re.I,
)
_SOFT_REJECT = re.compile(
    r"^\s*(no|nop|nope|cancel(ar)?|descarta(r)?|don'?t)[!?.\s]*$",
    re.I,
)


def classify_confirmation(message: str) -> ConfirmResult:
    """
    Classify user reply to a pending memory proposal.

    Labels: approve | reject | edit | ambiguous | topic_change.
    Silence/ambiguity must NEVER be treated as approval.
    """
    text = (message or "").strip()
    if not text:
        return ConfirmResult(label="ambiguous", confidence=0.0)

    edit_m = _EDIT.match(text)
    if edit_m:
        edited = (edit_m.group(1) or "").strip()
        if edited:
            return ConfirmResult(label="edit", edited_fact=edited, confidence=0.95)

    if _SOFT_APPROVE.match(text) or (_APPROVE.match(text) and len(text) < 48):
        return ConfirmResult(label="approve", confidence=0.9)

    if _SOFT_REJECT.match(text) or (_REJECT.match(text) and len(text) < 64):
        return ConfirmResult(label="reject", confidence=0.9)

    # Longer message that starts with yes/no but continues → treat carefully
    if _APPROVE.match(text) and len(text) < 80 and not _looks_like_new_question(text):
        return ConfirmResult(label="approve", confidence=0.7)

    if _REJECT.match(text) and len(text) < 80 and not _looks_like_new_question(text):
        return ConfirmResult(label="reject", confidence=0.7)

    if _looks_like_new_question(text):
        return ConfirmResult(label="topic_change", confidence=0.85)

    return ConfirmResult(label="ambiguous", confidence=0.4)


def _looks_like_new_question(text: str) -> bool:
    if "?" in text or "¿" in text:
        return True
    return bool(
        re.search(
            r"\b(qu[eé]|c[oó]mo|cu[aá]l|where|what|how|which|estado|stock|incidencia|ticket)\b",
            text,
            re.I,
        )
    )
