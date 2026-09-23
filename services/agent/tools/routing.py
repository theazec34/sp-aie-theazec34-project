"""Intent classification — RAG vs live tools (no user hint required)."""

from __future__ import annotations

import re
from typing import Literal

Intent = Literal["rag", "ticket", "inventory"]

_TICKET_HINT = re.compile(
    r"\b(ticket|incidencia|incident|soporte|reclamo|queja\s+registrad)\w*\b",
    re.IGNORECASE,
)
_TICKET_ID = re.compile(
    r"(?:ticket|incidencia|incident|id)\s*#?\s*(\d+)\b|\b#(\d+)\b",
    re.IGNORECASE,
)
_INVENTORY_HINT = re.compile(
    r"\b(inventario|stock|sku|ingrediente|producto|existencias|almac[eé]n)\w*\b",
    re.IGNORECASE,
)


def extract_ticket_id(question: str) -> int | None:
    match = _TICKET_ID.search(question or "")
    if not match:
        return None
    raw = match.group(1) or match.group(2)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def extract_product_query(question: str) -> str | None:
    """Best-effort product name after inventory keywords."""
    q = (question or "").strip()
    # "stock de lomo" / "inventario de carne"
    m = re.search(
        r"(?:stock|inventario|existencias|sku)\s+(?:de|del|de la|de los|de las)?\s*(.+)$",
        q,
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip(" ?¿¡!.")
        return name or None
    return None


def classify_intent(question: str) -> Intent:
    """Decide automatically whether the question needs RAG or a live tool."""
    q = (question or "").strip()
    if not q:
        return "rag"
    if _TICKET_HINT.search(q) or extract_ticket_id(q) is not None:
        return "ticket"
    if _INVENTORY_HINT.search(q):
        return "inventory"
    return "rag"
