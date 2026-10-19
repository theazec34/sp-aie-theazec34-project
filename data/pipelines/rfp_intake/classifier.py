"""Classifier agent — is this a Brasaland B2B RFP? Deterministic + structured."""

from __future__ import annotations

import re
from typing import Any

# Signals of a real RFP / LOI for Brasaland corporate opportunities
_RFP_HINTS = re.compile(
    r"("
    r"\brfp\b|request\s+for\s+proposal|solicitud\s+de\s+propuesta|"
    r"catering|concesi[oó]n|co-?brand|alianza|contrato|"
    r"proposal\s+request|letter\s+of\s+intent|carta\s+de\s+intenci[oó]n|"
    r"comensales|empleados|resort|event"
    r")",
    re.I,
)

_INVALID_FRANCHISE = re.compile(
    r"("
    r"franquicia|franchise\s+inquiry|quiero\s+abrir\s+un\s+local|"
    r"informaci[oó]n\s+general\s+sobre\s+franquicias"
    r")",
    re.I,
)

_CLIENT = re.compile(
    r"(?:cliente|client|empresa|company|from|de parte de)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ][\w\s&.\-]{2,60})",
    re.I,
)
_DEADLINE = re.compile(
    r"(?:"
    r"(?:deadline|fecha\s+l[ií]mite|due\s+date|responder\s+antes)[^\n.]{0,60}"
    r"|\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"
    r"|\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{1,2}(?:\s+\d{4})?"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    r")",
    re.I,
)
_SCOPE = re.compile(
    r"("
    r"(?:comensales|empleados|covers|pax)\s*[:=]?\s*\d+|"
    r"\d+\s+(?:comensales|empleados|covers|pax|resorts|ubicaciones)|"
    r"(?:ubicaciones|locations|resorts)\s*[:=]?\s*\d+|"
    r"contrato\s+de\s+\d+\s*meses|12\s*meses|catering\s+semanal|"
    r"\d+\s*[–\-]\s*\d+\s*k\s*usd"
    r")",
    re.I,
)
_BUDGET = re.compile(
    r"("
    r"USD\s*[\d,.]+(?:\s*[–\-]\s*[\d,.]+)?\s*(?:/?\s*a[nñ]o)?|"
    r"COP\s*[\d,.]+(?:\s*[–\-]\s*[\d,.]+)?(?:M)?\s*(?:/?\s*a[nñ]o)?|"
    r"\$\s*[\d,.]+|"
    r"\d[\d,.]*\s*[–\-]?\s*\d*[\d,.]*\s*k?\s*USD\s*/?\s*a[nñ]o|"
    r"(?:presupuesto|budget)[^\n.]{0,50}"
    r")",
    re.I,
)
_SERVICE = re.compile(
    r"("
    r"co-?branded?\s+(?:food\s+)?concession[^\n.]{0,40}|"
    r"catering\s+(?:corporativo|semanal|recurrente)[^\n.]{0,40}|"
    r"men[uú]\s+de\s+autor|men[uú]\s+est[aá]ndar|"
    r"concesi[oó]n\s+co-?branded?|exclusividad|"
    r"catering|concesi[oó]n|co-?brand|event\s+concession"
    r")",
    re.I,
)
_LOCATION = re.compile(
    r"("
    r"Florida(?:[^\n,]{0,40})?|Medell[ií]n(?:[^\n,]{0,30})?|"
    r"Bogot[aá]|Miami|Orlando|Tampa\s+Bay|Cali|Colombia|USA"
    r")",
    re.I,
)
_TRAINING_NEED = re.compile(
    r"("
    r"men[uú]\s+de\s+autor|receta\s+nueva|est[aá]ndar\s+nuevo|certificaci[oó]n|"
    r"training|capacitaci[oó]n|co-?branded\s+menu"
    r")",
    re.I,
)


def classify_rfp(markdown: str) -> dict[str, Any]:
    """
    Return structured classification.

    Criteria for NOT an RFP (BRIEFING §4.3):
    - Franchise / general inquiry without scope, budget, AND deadline.
    False negatives: prefer accepting informal LOIs that still have
    client + service + (scope OR deadline).
    """
    text = markdown or ""
    lower = text.lower()

    franchise = bool(_INVALID_FRANCHISE.search(text))
    has_rfp_lang = bool(_RFP_HINTS.search(text))
    has_deadline = bool(_DEADLINE.search(text))
    has_scope = bool(_SCOPE.search(text))
    has_budget = bool(_BUDGET.search(text))
    has_service = bool(_SERVICE.search(text))
    has_location = bool(_LOCATION.search(text))

    client = _extract_client(text)

    # Hard reject: franchise without commercial RFP signals
    if franchise and not (has_scope and has_deadline):
        return {
            "is_rfp": False,
            "confidence": 0.92,
            "notes": "Consulta de franquicia sin alcance/fecha límite — no es RFP B2B.",
            "client_name": client,
            "location": _first(_LOCATION, text),
            "service_type": None,
            "scope": None,
            "deadline": None,
            "budget_range": None,
            "departments_needed": [],
            "open_questions": [
                "Documento descartado: no es una RFP corporativa de Brasaland."
            ],
        }

    score = 0.0
    if has_rfp_lang:
        score += 0.25
    if client:
        score += 0.2
    if has_service:
        score += 0.2
    if has_scope:
        score += 0.15
    if has_deadline:
        score += 0.15
    if has_budget:
        score += 0.1
    if has_location:
        score += 0.05

    is_rfp = score >= 0.45 and bool(client or has_service) and (has_scope or has_deadline)

    departments = ["marketing", "operaciones", "procurement"]
    # Explicit opt-out: standard menu / no new recipes → skip training
    training_opt_out = bool(
        re.search(
            r"("
            r"men[uú]\s+est[aá]ndar|"
            r"sin\s+(?:recetas?\s+nuevas?|capacitaci[oó]n|training)|"
            r"no\s+requerimos\s+(?:capacitaci[oó]n|training|men[uú]\s+de\s+autor)|"
            r"solo\s+el\s+men[uú]\s+est[aá]ndar"
            r")",
            text,
            re.I,
        )
    )
    needs_training = (not training_opt_out) and (
        bool(_TRAINING_NEED.search(text))
        or bool(
            is_rfp
            and re.search(r"co-?brand|men[uú]\s+de\s+autor|exclusividad", text, re.I)
        )
    )
    if needs_training:
        departments.append("training")
    # Deduplicate preserve order
    seen: set[str] = set()
    departments = [d for d in departments if not (d in seen or seen.add(d))]

    open_q: list[str] = []
    if is_rfp and not has_budget:
        open_q.append("Presupuesto / budget_range no explícito en el documento.")
    if is_rfp and not has_deadline:
        open_q.append("Fecha límite de respuesta no explícita.")

    return {
        "is_rfp": is_rfp,
        "confidence": round(min(score, 0.99), 2),
        "notes": (
            "RFP/LOI aceptada."
            if is_rfp
            else "Documento sin señales suficientes de RFP B2B (cliente/servicio/alcance)."
        ),
        "client_name": client,
        "location": _first(_LOCATION, text),
        "service_type": _first(_SERVICE, text),
        "scope": _snip_scope(text),
        "deadline": _first(_DEADLINE, text),
        "budget_range": _first(_BUDGET, text),
        "departments_needed": departments if is_rfp else [],
        "open_questions": open_q,
    }


def _extract_client(text: str) -> str | None:
    # Prefer known seed clients
    for name in ("Sunset Bay Resorts", "Andes Tech Solutions", "Andes Tech"):
        if name.lower() in text.lower():
            return name if name != "Andes Tech" else "Andes Tech Solutions"
    m = _CLIENT.search(text)
    if m:
        return m.group(1).strip()
    # First titled line heuristic
    for line in text.splitlines()[:15]:
        line = line.strip("# ").strip()
        if 3 < len(line) < 80 and re.search(r"Resorts|Solutions|Corp|Inc|S\.A", line):
            return line
    return None


def _first(pat: re.Pattern[str], text: str) -> str | None:
    m = pat.search(text)
    return m.group(0).strip() if m else None


def _snip_scope(text: str) -> str | None:
    m = re.search(
        r"((?:\d+\s+[–\-]\s*)?\d+\s*(?:resorts|ubicaciones|comensales|empleados|covers)"
        r"|catering\s+semanal[^\n.]{0,40}"
        r"|contrato\s+de\s+\d+\s*meses"
        r"|.{0,20}(?:comensales|empleados|resorts|ubicaciones|12\s*meses).{0,40})",
        text,
        re.I,
    )
    if m:
        return m.group(1).strip()
    return _first(_SCOPE, text)
