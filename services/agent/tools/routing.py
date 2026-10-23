"""Intent classification — RAG vs live tools (no user hint required)."""

from __future__ import annotations

import re
from typing import Literal

Intent = Literal["rag", "ticket", "inventory", "supplier"]

_TICKET_HINT = re.compile(
    r"\b(ticket|incidencia|incident|soporte|reclamo|queja\s+registrad)\w*\b",
    re.IGNORECASE,
)
_TICKET_ID = re.compile(
    r"(?:ticket|incidencia|incident|id)\s*#?\s*(\d+)\b|\b#(\d+)\b",
    re.IGNORECASE,
)
_SUPPLIER_HINT = re.compile(
    r"\b(proveedor(?:es)?|supplier|tarifa|rate_per_unit|mayor\s+proveedor|"
    r"directorio\s+de\s+proveedor)\w*\b",
    re.IGNORECASE,
)
_INVENTORY_HINT = re.compile(
    r"\b(inventario|stock|sku|ingrediente|producto|existencias|almac[eé]n|"
    r"salida(?:s)?|entrada(?:s)?|historial|inbound|outbound|kg|kilos?|"
    r"merma\s+de\s+inventario)\w*\b",
    re.IGNORECASE,
)
_INVENTORY_OUTBOUND = re.compile(
    r"\b(salida(?:s)?|outbound|consumo|consumo\s+de\s+stock)\b",
    re.IGNORECASE,
)
_INVENTORY_INBOUND = re.compile(
    r"\b(entrada(?:s)?|inbound|recepci[oó]n|pedido(?:s)?\s+recibid)\b",
    re.IGNORECASE,
)
_INVENTORY_HISTORY = re.compile(
    r"\b(historial|movimientos?|orders?)\b",
    re.IGNORECASE,
)
_INVENTORY_SUMMARY = re.compile(
    r"\b(resumen|mayor|m[aá]s\s+kg|total(?:es)?|ranking|cu[aá]ntos?\s+kg)\b",
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
    m = re.search(
        r"(?:stock|inventario|existencias|sku)\s+(?:de|del|de la|de los|de las)?\s*(.+)$",
        q,
        re.IGNORECASE,
    )
    if m:
        name = m.group(1).strip(" ?¿¡!.")
        return name or None
    return None


def extract_inventory_view(
    question: str,
) -> Literal["stock", "summary", "history", "inbound", "outbound"]:
    """Which inventory MCP surface to call for this question."""
    q = question or ""
    if _INVENTORY_OUTBOUND.search(q):
        return "outbound"
    if _INVENTORY_INBOUND.search(q):
        return "inbound"
    if _INVENTORY_HISTORY.search(q):
        return "history"
    if _INVENTORY_SUMMARY.search(q) or re.search(
        r"\b(proveedor).*\b(kg|kilos?)\b|\b(kg|kilos?).*\b(proveedor)\b",
        q,
        re.IGNORECASE,
    ):
        return "summary"
    return "stock"


def extract_supplier_action(
    question: str,
) -> Literal["list", "top_rate", "summary"]:
    q = question or ""
    if re.search(
        r"\b(mayor|m[aá]s\s+caro|tarifa\s+m[aá]s\s+alta|top|ranking|€|euro)\b",
        q,
        re.IGNORECASE,
    ):
        return "top_rate"
    if re.search(r"\b(lista|listado|todos|directorio)\b", q, re.IGNORECASE):
        return "list"
    return "summary"


def classify_intent(question: str) -> Intent:
    """Decide automatically whether the question needs RAG or a live tool."""
    q = (question or "").strip()
    if not q:
        return "rag"
    if _TICKET_HINT.search(q) or extract_ticket_id(q) is not None:
        return "ticket"
    # Supplier+kg → inventory summary (joins inbound qty with tariffs).
    if _SUPPLIER_HINT.search(q) and re.search(r"\b(kg|kilos?|entrada)\b", q, re.I):
        return "inventory"
    if _SUPPLIER_HINT.search(q):
        return "supplier"
    if _INVENTORY_HINT.search(q):
        return "inventory"
    return "rag"
