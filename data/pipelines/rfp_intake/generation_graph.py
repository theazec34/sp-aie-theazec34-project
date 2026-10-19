"""Parte 2: generador ↔ evaluadores por departamento (ciclo con límite).

Consume el handoff de Parte 1 (ticket_id + synthesizer / key_aspects).
No re-parsea el PDF.
"""

from __future__ import annotations

from typing import Any, TypedDict

from data.pipelines.rfp_intake.evaluators import evaluate_section
from data.pipelines.rfp_intake.generators import generate_section
from data.pipelines.rfp_intake.guidelines import MAX_GENERATOR_ITERATIONS
from data.pipelines.rfp_intake.knowledge_hints import (
    fetch_knowledge_snippets,
    knowledge_query_for_department,
)


class SectionWork(TypedDict, total=False):
    department_id: str
    contact_name: str | None
    key_aspects: list[str]
    open_questions: list[str]
    draft_content: str
    evaluation_results: dict[str, Any]
    iteration: int
    needs_human_review: bool
    section_status: str  # generando | en_evaluacion | aprobado_auto | needs_human_review


def run_section_cycle(
    department_id: str,
    *,
    metadata: dict[str, Any],
    key_aspects: list[str],
    open_questions: list[str] | None = None,
    contact_name: str | None = None,
    max_iterations: int = MAX_GENERATOR_ITERATIONS,
    use_knowledge: bool = True,
) -> SectionWork:
    """Ciclo generador-evaluador para una sección (aislado del resto)."""
    feedback: str | None = None
    draft = ""
    evaluation: dict[str, Any] = {}
    snippets: list[str] = []
    if use_knowledge:
        snippets = fetch_knowledge_snippets(
            knowledge_query_for_department(department_id, metadata)
        )

    for iteration in range(1, max_iterations + 1):
        draft = generate_section(
            department_id,
            metadata=metadata,
            key_aspects=key_aspects,
            open_questions=open_questions,
            feedback=feedback,
            knowledge_snippets=snippets,
        )
        evaluation = evaluate_section(
            department_id=department_id,
            draft=draft,
            key_aspects=key_aspects,
            metadata=metadata,
        )
        if evaluation.get("overall_pass"):
            return {
                "department_id": department_id,
                "contact_name": contact_name,
                "key_aspects": key_aspects,
                "open_questions": list(open_questions or []),
                "draft_content": draft,
                "evaluation_results": evaluation,
                "iteration": iteration,
                "needs_human_review": False,
                "section_status": "aprobado_auto",
            }
        feedback = evaluation.get("feedback_for_generator") or feedback

    # Límite agotado: conservar último borrador + EvaluationResult
    return {
        "department_id": department_id,
        "contact_name": contact_name,
        "key_aspects": key_aspects,
        "open_questions": list(open_questions or []),
        "draft_content": draft,
        "evaluation_results": evaluation,
        "iteration": max_iterations,
        "needs_human_review": True,
        "section_status": "needs_human_review",
    }


def run_response_generation(
    *,
    ticket_id: int,
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
    max_iterations: int = MAX_GENERATOR_ITERATIONS,
) -> dict[str, Any]:
    """
    Orquesta Parte 2 para todos los departamentos del handoff.

    Estados de ticket (lado runner):
      generando_borrador → en_evaluacion → borrador_listo | needs_human_review
    """
    if not sections:
        return {
            "ticket_id": ticket_id,
            "status": "fallido",
            "error": "Sin secciones de departamento en el handoff de Parte 1.",
            "sections": [],
        }

    results: list[SectionWork] = []
    # Secciones en paralelo (cada una con su propio ciclo gen↔eval)
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=min(4, len(sections))) as pool:
        futs = {
            pool.submit(
                run_section_cycle,
                sec["department_id"],
                metadata=metadata,
                key_aspects=list(sec.get("key_aspects") or []),
                open_questions=list(sec.get("open_questions") or []),
                contact_name=sec.get("contact_name"),
                max_iterations=max_iterations,
            ): sec["department_id"]
            for sec in sections
        }
        by_id: dict[str, SectionWork] = {}
        for fut in as_completed(futs):
            by_id[futs[fut]] = fut.result()
        # Orden estable según handoff
        for sec in sections:
            results.append(by_id[sec["department_id"]])

    any_human = any(r.get("needs_human_review") for r in results)
    all_pass = all(
        (r.get("evaluation_results") or {}).get("overall_pass") for r in results
    )
    if any_human or not all_pass:
        status = "needs_human_review"
    else:
        # Éxito Parte 2 → listo para Parte 3 (sin usar esperando_aprobación aún)
        status = "borrador_listo"

    return {
        "ticket_id": ticket_id,
        "status": status,
        "sections": results,
        "part3_handoff": {
            "ready": True,
            "ticket_id": ticket_id,
            "requires": ["draft_content", "evaluation_results", "needs_human_review"],
            "note": (
                "Secciones con needs_human_review deben revisarse en Parte 3; "
                "no se usa esperando_aprobación todavía."
            ),
        },
    }
