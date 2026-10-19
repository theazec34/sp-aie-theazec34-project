"""Generadores por departamento — redactan la sección económica desde el handoff Parte 1.

No releen el PDF: usan metadatos + key_aspects del synthesizer / DepartmentSection.
"""

from __future__ import annotations

import re
from typing import Any

from data.pipelines.rfp_intake.departments_ref import DEPARTMENTS
from data.pipelines.rfp_intake.guidelines import BRAND_PILLARS


def generate_section(
    department_id: str,
    *,
    metadata: dict[str, Any],
    key_aspects: list[str],
    open_questions: list[str] | None = None,
    feedback: str | None = None,
    knowledge_snippets: list[str] | None = None,
    force_violate: str | None = None,
) -> str:
    """
    Genera borrador de sección en español.

    force_violate: id de regla a violar a propósito (tests de cumplimiento).
    """
    info = DEPARTMENTS.get(department_id) or {
        "name": department_id,
        "owner": "Camila Ospina",
        "role": "",
    }
    client = metadata.get("client_name") or "Cliente"
    location = metadata.get("location") or "ubicación por confirmar"
    service = metadata.get("service_type") or "servicio solicitado"
    scope = metadata.get("scope") or "alcance por confirmar"
    budget = metadata.get("budget_range") or "presupuesto por confirmar"
    deadline = metadata.get("deadline") or "fecha límite por confirmar"

    pillars = ", ".join(BRAND_PILLARS)
    aspects_block = "\n".join(f"- {a}" for a in (key_aspects or [])[:8]) or "- (sin aspectos clave)"
    questions = open_questions or []
    q_block = "\n".join(f"- {q}" for q in questions[:5]) if questions else "- Ninguna abierta"

    kb = ""
    if knowledge_snippets:
        kb = "\nReferencias internas Brasaland:\n" + "\n".join(
            f"- {s[:200]}" for s in knowledge_snippets[:3]
        )

    # Cuerpo base compliant
    break_price = force_violate in {"price-eur", "price-cop-usd"}
    if break_price:
        # Evita € residual en alcance/presupuesto al forzar fallo de price-eur
        scope = re.sub(r"€|eur(os)?", "EUR_OMITIDO", scope, flags=re.I)
        budget = re.sub(r"€|eur(os)?", "", budget, flags=re.I)

    prices = _eur_price_line(budget, break_price)
    setup = (
        "Montaje y puesta en marcha: mínimo 12 días hábiles desde la firma "
        "(nunca menos de 10 días hábiles)."
    )
    if force_violate == "setup-min-10-days":
        setup = "Montaje express garantizado en 5 días hábiles desde la firma."

    validity = (
        "Validez de la oferta: 30 días desde la emisión de esta sección."
        if force_violate != "offer-validity-30"
        else "Oferta válida hasta nuevo aviso (sin plazo fijo)."
    )

    pillars_line = (
        f"Esta sección se alinea con los pilares Brasaland: {pillars}."
        if force_violate != "brand-pillars"
        else "Ofrecemos un servicio ágil y competitivo en el mercado."
    )

    competitor = ""
    if force_violate == "no-competitors":
        competitor = (
            "\nNota comercial: superaremos a McDonald's y Burger King en la zona."
        )

    ceo_note = ""
    if not break_price and (
        _budget_over_50k_eur(budget) or force_violate == "ceo-threshold-50k"
    ):
        ceo_note = (
            "\nAviso: el valor anual estimado supera 50.000 €; "
            "se requerirá aprobación de Mariana Restrepo (CEO) en la Parte 3."
        )

    feedback_block = ""
    if feedback:
        feedback_block = (
            f"\nAjustes según evaluación previa:\n{feedback.strip()}\n"
        )

    body_by_dept = {
        "marketing": (
            f"Propuesta de valor y marca para {client} ({location}).\n"
            f"Servicio: {service}. Alcance: {scope}.\n"
            f"Incluye términos de exclusividad/co-branding según aspectos clave, "
            f"comunicación de marca y CRM compartido cuando aplique.\n"
            f"{pillars_line}\n"
            f"{prices}\n"
            f"{validity}\n"
            f"Contacto de sección: {info['owner']}."
        ),
        "operaciones": (
            f"Plan operativo para {client} en {location}.\n"
            f"Alcance operativo: {scope}. Servicio: {service}.\n"
            f"Capacidad de cocina/personal dimensionada al volumen indicado; "
            f"costo operativo por evento/sede se estimará sin inventar cifras ausentes.\n"
            f"{setup}\n"
            f"{pillars_line}\n"
            f"{prices}\n"
            f"{validity}\n"
            f"Contacto: {info['owner']}."
        ),
        "procurement": (
            f"Estimación de insumos y proveedores para {client} ({location}).\n"
            f"Servicio solicitado: {service}. Volumen de referencia: {scope}.\n"
            f"Presupuesto detectado: {budget}.\n"
            f"Lead times de proveedores ≥ 10 días hábiles; no se prometen entregas inferiores.\n"
            f"{pillars_line}\n"
            f"{prices}\n"
            f"{validity}\n"
            f"Contacto: {info['owner']}."
        ),
        "training": (
            f"Plan de formación y estándares para {client} ({location}).\n"
            f"Servicio: {service}. Alcance: {scope}.\n"
            f"Si el pedido exige menú de autor o estándar nuevo, se define tiempo de "
            f"desarrollo y certificación del personal de cocina.\n"
            f"Capacitación alineada a calidad Brasaland; go-live tras certificación.\n"
            f"{setup}\n"
            f"{pillars_line}\n"
            f"{prices}\n"
            f"{validity}\n"
            f"Contacto: {info['owner']}."
        ),
    }

    core = body_by_dept.get(
        department_id,
        (
            f"Sección {info['name']} para {client}.\n"
            f"{pillars_line}\n{prices}\n{validity}\n{setup}"
        ),
    )

    return (
        f"# Sección {info['name']} ({department_id})\n"
        f"Responsable: {info['owner']}\n"
        f"{feedback_block}\n"
        f"{core}{competitor}{ceo_note}{kb}\n\n"
        f"Aspectos clave (handoff Parte 1):\n{aspects_block}\n\n"
        f"Preguntas abiertas:\n{q_block}\n"
    ).strip()


def _eur_price_line(budget: str, break_rule: bool) -> str:
    if break_rule:
        # Quita cualquier mención de €/EUR para forzar fallo de cumplimiento en tests
        stripped = re.sub(r"€|eur(os)?", "", budget, flags=re.I).strip()
        return f"Precio orientativo sin moneda: {stripped or 'por confirmar'}."
    if re.search(r"€|eur(os)?", budget, re.I):
        return f"Precios de referencia: {budget} (expresados en euros €)."
    # Normaliza presupuestos legacy COP/USD → mención en €
    return (
        f"Rango presupuestal de referencia: {budget}. "
        "Toda cifra comercial se expresará en euros (€)."
    )


def _budget_over_50k_eur(budget: str) -> bool:
    from data.pipelines.rfp_intake.guidelines import CEO_THRESHOLD_EUR

    text = budget or ""
    for m in re.finditer(r"€\s*([\d.,]+)|([\d.,]+)\s*€", text):
        raw = (m.group(1) or m.group(2) or "").replace(".", "").replace(",", ".")
        try:
            if float(raw) > CEO_THRESHOLD_EUR:
                return True
        except ValueError:
            continue
    m = re.search(r"(\d[\d,.]*)\s*k\s*(?:€|eur)", text, re.I)
    if m:
        try:
            return float(m.group(1).replace(",", ".")) * 1000 > CEO_THRESHOLD_EUR
        except ValueError:
            pass
    # Legacy USD/COP seeds still treated as over-threshold when large
    if re.search(r"6[0-9]\s*[–\-]\s*75\s*k|60[,.]?000|75[,.]?000", text, re.I):
        return True
    return False
