"""Lineamientos BRIEFING §5 — moneda única: euro (€). Español."""

from __future__ import annotations

# Reglas objetivas (no opiniones). El evaluador reporta rule_ids / violations.
COMPLIANCE_RULES: dict[str, str] = {
    "price-eur": "Todo precio debe expresarse en euros (€).",
    "brand-pillars": (
        "Toda propuesta debe mencionar los tres pilares: "
        "calidad consistente, experiencia cálida, velocidad de servicio."
    ),
    "setup-min-10-days": (
        "Ninguna sección puede prometer montaje/entrega menores a 10 días hábiles."
    ),
    "no-competitors": "Ninguna propuesta puede mencionar nombres de competidores.",
    "offer-validity-30": (
        "Toda propuesta debe incluir un período de validez de la oferta "
        "(30 días desde su emisión)."
    ),
    "ceo-threshold-50k": (
        "Contratos estimados > 50.000 €/año requieren aprobación adicional de la CEO "
        "(Mariana Restrepo) antes del documento final (Parte 3)."
    ),
}

# Alias legacy → canónico (por si llegan borradores antiguos)
RULE_ID_ALIASES = {
    "price-cop-usd": "price-eur",
}

COMPETITOR_NAMES = (
    "mcdonald",
    "burger king",
    "kfc",
    "subway",
    "dominos",
    "domino's",
    "starbucks",
    "wendys",
    "wendy’s",
)

BRAND_PILLARS = (
    "calidad consistente",
    "experiencia cálida",
    "velocidad de servicio",
)

# Límites de iteración
MAX_GENERATOR_ITERATIONS = 3
MAX_APPROVAL_ITERATIONS = 3  # reject / request_changes por departamento

# Umbral CEO (euros anuales)
CEO_THRESHOLD_EUR = 50_000

# Árbitros fijos BRIEFING §7 (no LLM)
ARBITRATION_TRIGGERS = {
    "cost-vs-feasibility": {
        "arbiter": "Camila Ospina",
        "department_id": "marketing",
        "rule": (
            "Subir precio o reducir alcance; forzar request_changes "
            "en la(s) sección(es) desalineada(s)."
        ),
    },
    "setup-sla-breach": {
        "arbiter": "Felipe Guerrero",
        "department_id": "operaciones",
        "rule": "Forzar request_changes hasta ≥10 días hábiles en todas las secciones.",
    },
    "ceo-threshold": {
        "arbiter": "Mariana Restrepo",
        "department_id": "ceo",
        "rule": "Bloquear síntesis final hasta approve de CEO; rechazo si la CEO rechaza.",
    },
}
