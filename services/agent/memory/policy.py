"""What may / must never enter agent memory — CONTEXT-agent-memory.es.md."""

from __future__ import annotations

import re

from agent.memory.models import MemoryCategory

# Hard bans (never memorize)
_FORBIDDEN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(nómina|nomina|salario|sueldo|payroll|compensation|wage)\b",
            re.I,
        ),
        "payroll_or_compensation",
    ),
    (
        re.compile(
            r"\b(brasa\s*points|cliente|customer)\b.{0,40}\b(email|teléfono|telefono|phone|dni|ssn|dirección|direccion)\b",
            re.I,
        ),
        "customer_pii",
    ),
    (
        re.compile(
            r"\b(ssn|social security|número de cuenta|numero de cuenta|credit card|tarjeta)\b",
            re.I,
        ),
        "sensitive_pii",
    ),
]

# One-off / non-recurring signals → do not propose
_NON_MEMORABLE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(ticket promedio|average ticket|ayer|yesterday|hoy|today)\b",
            re.I,
        ),
        "one_off_metric_query",
    ),
    (
        re.compile(
            r"^(gracias|thanks|thank you|ok|vale|perfecto|listo)[\s!.]*$",
            re.I,
        ),
        "conversation_close",
    ),
    (
        re.compile(
            r"\b(traduce|translate|traducir|en inglés|in english)\b",
            re.I,
        ),
        "one_shot_task",
    ),
]

# Memorable operational signals
_MEMORABLE_PATTERNS: list[tuple[re.Pattern[str], MemoryCategory]] = [
    (
        re.compile(
            r"\b(cierra|abre|horario|closes?|opens?|hours?)\b.{0,60}\b(\d{1,2}\s*(am|pm|:)|fin(es)? de semana|weekend)",
            re.I,
        ),
        MemoryCategory.HOURS,
    ),
    (
        re.compile(
            r"\b(proveedor|supplier|entrega|deliver(y|s)?)\b.{0,80}\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            re.I,
        ),
        MemoryCategory.SUPPLIER,
    ),
    (
        re.compile(
            r"\b(apagón|apagon|corte de luz|outage|sin ventas|zero sales|no fue (un )?error|known issue)\b",
            re.I,
        ),
        MemoryCategory.INCIDENT_PATTERN,
    ),
    (
        re.compile(
            r"\b(siempre pide|always (ask|want|prefer)|formato|reportes? en)\b",
            re.I,
        ),
        MemoryCategory.COMM_PREFERENCE,
    ),
    (
        re.compile(
            r"\b(en realidad|actually|no los|not the|cambió|changed|corrige|correction)\b",
            re.I,
        ),
        MemoryCategory.OTHER_OPERATIONAL,
    ),
]

_LOCATION_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bmedell[ií]n\b", re.I), "medellin"),
    (re.compile(r"\bbogot[aá]\b", re.I), "bogota"),
    (re.compile(r"\bcali\b", re.I), "cali"),
    (re.compile(r"\bbarranquilla\b", re.I), "barranquilla"),
    (re.compile(r"\bmiami\s*beach\b", re.I), "miami_beach"),
    (re.compile(r"\bmiami\b", re.I), "miami"),
    (re.compile(r"\borlando\b", re.I), "orlando"),
    (re.compile(r"\bfort\s*lauderdale\b", re.I), "fort_lauderdale"),
    (re.compile(r"\blocation\s*(\d+)\b", re.I), "location_{n}"),
    (re.compile(r"\bzaragoza\b", re.I), "zaragoza"),
]


def detect_language(text: str) -> str:
    en_hits = len(re.findall(r"\b(the|and|please|thanks|actually|closes?|opens?)\b", text, re.I))
    es_hits = len(re.findall(r"\b(el|la|los|las|gracias|entrega|cierra|proveedor)\b", text, re.I))
    return "en" if en_hits > es_hits else "es"


def extract_location(text: str) -> str | None:
    for pat, loc in _LOCATION_HINTS:
        m = pat.search(text)
        if not m:
            continue
        if "{n}" in loc:
            return loc.format(n=m.group(1))
        return loc
    return None


def forbidden_reason(text: str) -> str | None:
    for pat, code in _FORBIDDEN_PATTERNS:
        if pat.search(text):
            return code
    return None


def non_memorable_reason(text: str) -> str | None:
    for pat, code in _NON_MEMORABLE_PATTERNS:
        if pat.search(text):
            return code
    return None


def detect_category(text: str) -> MemoryCategory | None:
    for pat, cat in _MEMORABLE_PATTERNS:
        if pat.search(text):
            return cat
    return None


def is_correction_signal(text: str) -> bool:
    return bool(
        re.search(
            r"\b(en realidad|actually|no (?:los|las|fue)|not (?:the|an?)|cambió|changed|"
            r"corrige|incorrecto|wrong|entrega los|closes? at|siempre pide)\b",
            text,
            re.I,
        )
    )
