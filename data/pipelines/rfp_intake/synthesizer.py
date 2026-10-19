"""Synthesizer — Sales handoff: what to ask from whom."""

from __future__ import annotations

from typing import Any

from data.pipelines.rfp_intake.departments_ref import DEPARTMENTS


def synthesize(
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build Part-1 handoff payload for Marketing/Sales (Camila)."""
    by_dept: list[dict[str, Any]] = []
    all_questions: list[str] = list(metadata.get("open_questions") or [])

    for sec in sections:
        dept = sec.get("department_id") or ""
        info = DEPARTMENTS.get(dept, {})
        qs = list(sec.get("open_questions") or [])
        all_questions.extend(qs)
        by_dept.append(
            {
                "department_id": dept,
                "department_name": info.get("name", dept),
                "contact": sec.get("contact_name") or info.get("owner"),
                "ask_them": sec.get("key_aspects") or [],
                "open_questions": qs,
            }
        )

    # Dedup questions
    seen: set[str] = set()
    uniq_q: list[str] = []
    for q in all_questions:
        k = q.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq_q.append(q)

    summary_lines = [
        f"Cliente: {metadata.get('client_name') or 'N/D'}",
        f"Ubicación: {metadata.get('location') or 'N/D'}",
        f"Servicio: {metadata.get('service_type') or 'N/D'}",
        f"Alcance: {metadata.get('scope') or 'N/D'}",
        f"Fecha límite: {metadata.get('deadline') or 'N/D'}",
        f"Presupuesto: {metadata.get('budget_range') or 'por confirmar'}",
        f"Departamentos: {', '.join(metadata.get('departments_needed') or [])}",
    ]

    return {
        "ticket_owner": "Camila Ospina",
        "sales_brief": "Qué pedir a cada departamento (sin releer el PDF):",
        "summary_lines": summary_lines,
        "departments": by_dept,
        "open_questions": uniq_q,
        "part2_handoff": {
            "ready": True,
            "requires": ["ticket_id", "synthesizer_payload", "department_sections"],
            "next_statuses": ["generando_borrador"],
        },
        "readability": {
            "flesch_kincaid": metadata.get("flesch_kincaid"),
            "gunning_fog": metadata.get("gunning_fog"),
            "word_count": metadata.get("word_count"),
        },
    }


def merge_worker_conflicts(sections: list[dict[str, Any]]) -> list[str]:
    """
    Design: if two workers contradict on the same numeric claim, surface both
    as open_questions for Camila — do not auto-resolve in Part 1.
    """
    notes: list[str] = []
    nums: dict[str, list[str]] = {}
    for sec in sections:
        for aspect in sec.get("key_aspects") or []:
            for m in __import__("re").finditer(r"(\d[\d,.]*)", aspect):
                nums.setdefault(m.group(1), []).append(
                    f"{sec.get('department_id')}: {aspect[:80]}"
                )
    for val, refs in nums.items():
        depts = {r.split(":")[0] for r in refs}
        if len(depts) > 1 and len(refs) > 1:
            notes.append(
                f"Posible contradicción en cifra '{val}' entre {sorted(depts)} — "
                "revisión humana (Camila)."
            )
    return notes
