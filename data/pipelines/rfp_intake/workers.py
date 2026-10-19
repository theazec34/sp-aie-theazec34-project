"""Workers por departamento — extraen key_aspects del documento (sin inventar cifras)."""

from __future__ import annotations

import re
from typing import Any

from data.pipelines.rfp_intake.departments_ref import DEPARTMENTS


def run_worker(
    department_id: str,
    markdown: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Extract department-relevant key aspects; missing figures → open_questions."""
    info = DEPARTMENTS.get(department_id)
    if info is None:
        return {
            "department_id": department_id,
            "contact_name": "Camila Ospina",
            "key_aspects": [],
            "open_questions": [
                f"Departamento '{department_id}' no está en el BRIEFING; "
                "escalar a marketing (dueña del ticket)."
            ],
        }

    text = markdown or ""
    aspects: list[str] = []
    open_q: list[str] = []

    if department_id == "marketing":
        aspects.extend(_find_all(
            text,
            [
                r"exclusividad[^\n.]{0,80}",
                r"co-?brand[^\n.]{0,80}",
                r"validez[^\n.]{0,60}",
                r"marca[^\n.]{0,60}",
                r"propuesta[^\n.]{0,80}",
            ],
        ))
        if metadata.get("client_name"):
            aspects.insert(0, f"Cliente: {metadata['client_name']}")
        if metadata.get("deadline"):
            aspects.append(f"Fecha límite mencionada: {metadata['deadline']}")
        if not any("validez" in a.lower() for a in aspects):
            open_q.append("Confirmar período de validez de la oferta (lineamiento: 30 días).")

    elif department_id == "operaciones":
        aspects.extend(_find_all(
            text,
            [
                r"(montaje|setup|capacidad|cocina|personal|turno)[^\n.]{0,90}",
                r"(comensales|empleados|covers|pax)\s*[:=]?\s*\d+[^\n.]{0,40}",
                r"(ubicaciones|locations|resorts)\s*[:=]?\s*\d+[^\n.]{0,40}",
                r"(semanal|diario|evento)[^\n.]{0,60}",
            ],
        ))
        if not re.search(r"\d+\s*(d[ií]as|days)", text, re.I):
            open_q.append(
                "Plazo de montaje/entrega no explícito — no asumir <10 días hábiles."
            )
        if not re.search(r"\d+", text):
            open_q.append("Volumen/comensales no numérico en el documento.")

    elif department_id == "procurement":
        aspects.extend(_find_all(
            text,
            [
                r"(insumo|proveedor|supplier|volumen|costo|budget|presupuesto)[^\n.]{0,90}",
                r"(USD|COP)\s*[\d,.]+\s*(?:/?\s*a[nñ]o)?[^\n.]{0,40}",
                r"(lead\s*time|entrega|delivery)[^\n.]{0,60}",
            ],
        ))
        if not metadata.get("budget_range") and not re.search(r"USD|COP|\$", text):
            open_q.append("Sin cifra de presupuesto en la RFP — no inventar costo.")
        if metadata.get("budget_range"):
            aspects.append(f"Rango presupuesto detectado: {metadata['budget_range']}")

    elif department_id == "training":
        aspects.extend(_find_all(
            text,
            [
                r"(men[uú]\s+de\s+autor|receta|est[aá]ndar|certificaci[oó]n|capacitaci[oó]n|"
                r"training|calidad)[^\n.]{0,90}",
            ],
        ))
        if not aspects:
            open_q.append(
                "No hay señal clara de menú/estándar nuevo; confirmar si Formación aplica."
            )

    # Dedup / trim
    clean: list[str] = []
    seen: set[str] = set()
    for a in aspects:
        a = a.strip(" -•\t")
        key = a.lower()
        if len(a) < 8 or key in seen:
            continue
        seen.add(key)
        clean.append(a[:240])
    if not clean:
        clean.append(
            f"Revisar extractos de {info['name']} — sin bullets explícitos en el PDF."
        )
        open_q.append("Faltan detalles específicos para este departamento en el documento.")

    return {
        "department_id": department_id,
        "contact_name": info["owner"],
        "key_aspects": clean[:12],
        "open_questions": open_q,
    }


def _find_all(text: str, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for pat in patterns:
        for m in re.finditer(pat, text, re.I):
            hits.append(m.group(0).strip())
    return hits
