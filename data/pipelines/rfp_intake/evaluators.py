"""Evaluadores en paralelo: legibilidad, pertinencia y cumplimiento BRIEFING §5."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from data.pipelines.rfp_intake.convert import compute_readability
from data.pipelines.rfp_intake.guidelines import (
    BRAND_PILLARS,
    COMPETITOR_NAMES,
    COMPLIANCE_RULES,
)


def evaluate_readability(draft: str) -> dict[str, Any]:
    metrics = compute_readability(draft)
    words = int(metrics.get("word_count") or 0)
    fk = metrics.get("flesch_kincaid")
    fog = metrics.get("gunning_fog")
    # Umbral práctico: texto usable para Sales (no vacío, no ilegalmente corto)
    passed = words >= 40
    details = (
        f"palabras={words}; flesch_kincaid={fk}; gunning_fog={fog}. "
        "Se espera un borrador legible (≥40 palabras) para la propuesta económica."
    )
    feedback = "" if passed else "Amplía el borrador (≥40 palabras) con proposición clara y cifras duales."
    return {
        "pass": passed,
        "score": float(fk) if fk is not None else None,
        "details": details,
        "feedback": feedback,
    }


def evaluate_relevance(
    draft: str,
    *,
    key_aspects: list[str],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    text = (draft or "").lower()
    missing: list[str] = []
    client = (metadata.get("client_name") or "").strip()
    if client and client.lower() not in text:
        missing.append(f"cliente:{client}")
    # Al menos un aspecto clave debe reflejarse (token significativo)
    covered = 0
    for aspect in key_aspects or []:
        tokens = [t for t in re.split(r"\W+", aspect.lower()) if len(t) > 4][:3]
        if tokens and any(t in text for t in tokens):
            covered += 1
    if (key_aspects or []) and covered == 0:
        missing.append("aspectos_clave_handoff")
    for field, label in (
        ("service_type", "tipo_servicio"),
        ("location", "ubicacion"),
    ):
        val = (metadata.get(field) or "").strip()
        if not val:
            continue
        # token significativo del valor (evita falsos negativos con guiones)
        tok = [t for t in re.split(r"[\W_]+", val.lower()) if len(t) > 4][:3]
        if tok and not any(t in text for t in tok):
            missing.append(label)

    passed = len(missing) == 0
    feedback = ""
    if not passed:
        feedback = (
            "Incorpora lo faltante del handoff Parte 1: " + ", ".join(missing) + "."
        )
    return {
        "pass": passed,
        "missing_aspects": missing,
        "feedback": feedback,
    }


def evaluate_compliance(draft: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    text = draft or ""
    lower = text.lower()
    violations: list[str] = []
    rule_ids: list[str] = []

    # price-eur
    has_eur = bool(re.search(r"€|\beur(os)?\b", lower))
    if not has_eur:
        rule_ids.append("price-eur")
        violations.append(COMPLIANCE_RULES["price-eur"])

    # brand-pillars
    if not all(p in lower for p in BRAND_PILLARS):
        rule_ids.append("brand-pillars")
        violations.append(COMPLIANCE_RULES["brand-pillars"])

    # setup-min-10-days — busca promesas < 10 días
    for m in re.finditer(
        r"(\d+)\s*días\s*hábiles",
        lower,
    ):
        days = int(m.group(1))
        if days < 10:
            rule_ids.append("setup-min-10-days")
            violations.append(
                f"{COMPLIANCE_RULES['setup-min-10-days']} (encontrado: {days} días)"
            )
            break
    # "en N días" genérico cerca de montaje/entrega
    if "setup-min-10-days" not in rule_ids:
        for m in re.finditer(
            r"(montaje|entrega|puesta en marcha|setup)[^\n.]{0,40}?(\d+)\s*días",
            lower,
        ):
            days = int(m.group(2))
            if days < 10:
                rule_ids.append("setup-min-10-days")
                violations.append(
                    f"{COMPLIANCE_RULES['setup-min-10-days']} (encontrado: {days} días)"
                )
                break

    # no-competitors
    for name in COMPETITOR_NAMES:
        if name in lower:
            rule_ids.append("no-competitors")
            violations.append(COMPLIANCE_RULES["no-competitors"])
            break

    # offer-validity-30
    if not re.search(r"30\s*días", lower) or not re.search(
        r"validez|válida|valida", lower
    ):
        rule_ids.append("offer-validity-30")
        violations.append(COMPLIANCE_RULES["offer-validity-30"])

    # ceo-threshold: solo marca violación si el presupuesto >50k y el borrador
    # niega o omite el aviso CEO cuando debería mencionarlo (soft: no falla si omite;
    # fallamos solo si niega la necesidad)
    meta = metadata or {}
    budget = str(meta.get("budget_range") or "")
    if re.search(r"no\s+requiere\s+aprobaci[oó]n\s+(de\s+la\s+)?ceo", lower):
        rule_ids.append("ceo-threshold-50k")
        violations.append(COMPLIANCE_RULES["ceo-threshold-50k"])

    # Dedup rule_ids
    seen: set[str] = set()
    uniq_ids: list[str] = []
    for r in rule_ids:
        if r not in seen:
            seen.add(r)
            uniq_ids.append(r)

    passed = len(uniq_ids) == 0
    feedback = ""
    if not passed:
        feedback = "Corrige cumplimiento BRIEFING: " + "; ".join(uniq_ids) + "."
    return {
        "pass": passed,
        "rule_ids": uniq_ids,
        "violations": violations,
        "feedback": feedback,
        "budget_hint": budget[:80],
    }


def evaluate_section(
    *,
    department_id: str,
    draft: str,
    key_aspects: list[str],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Ejecuta los tres evaluadores en paralelo y consolida EvaluationResult."""
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(evaluate_readability, draft): "readability",
            pool.submit(
                evaluate_relevance, draft, key_aspects=key_aspects, metadata=metadata
            ): "relevance",
            pool.submit(evaluate_compliance, draft, metadata=metadata): "compliance",
        }
        for fut in as_completed(futures):
            key = futures[fut]
            results[key] = fut.result()

    readability = results["readability"]
    relevance = results["relevance"]
    compliance = results["compliance"]
    overall = bool(
        readability.get("pass") and relevance.get("pass") and compliance.get("pass")
    )
    feedback_parts = [
        readability.get("feedback") or "",
        relevance.get("feedback") or "",
        compliance.get("feedback") or "",
    ]
    feedback = " ".join(p for p in feedback_parts if p).strip()
    if not feedback and not overall:
        feedback = "Revisa legibilidad, pertinencia y cumplimiento del BRIEFING."

    return {
        "section_id": department_id,
        "department_id": department_id,
        "readability": {
            "pass": readability["pass"],
            "score": readability.get("score"),
            "details": readability.get("details"),
        },
        "relevance": {
            "pass": relevance["pass"],
            "missing_aspects": relevance.get("missing_aspects") or [],
        },
        "compliance": {
            "pass": compliance["pass"],
            "rule_ids": compliance.get("rule_ids") or [],
            "violations": compliance.get("violations") or [],
        },
        "overall_pass": overall,
        "feedback_for_generator": feedback,
    }
