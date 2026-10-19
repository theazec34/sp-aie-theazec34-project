"""Lineamientos BRIEFING §5 — ids estables para el evaluador de cumplimiento."""

from __future__ import annotations

# Reglas objetivas (no opiniones). El evaluador reporta rule_ids / violations.
COMPLIANCE_RULES: dict[str, str] = {
    "price-cop-usd": "Todo precio debe expresarse en COP y en USD.",
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
        "Contratos estimados > 50.000 USD/año requieren aprobación adicional de la CEO "
        "(Mariana Restrepo) antes del documento final (Parte 3)."
    ),
}

# Competidores prohibidos (señales típicas en borradores)
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

# Límite del ciclo generador ↔ evaluador por sección
MAX_GENERATOR_ITERATIONS = 3
