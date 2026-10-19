"""Tests Parte 2: generador, evaluadores y fallo de cumplimiento BRIEFING."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO, _REPO / "services", _REPO / "services" / "api"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.pipelines.rfp_intake.evaluators import (  # noqa: E402
    evaluate_compliance,
    evaluate_section,
)
from data.pipelines.rfp_intake.generation_graph import (  # noqa: E402
    run_response_generation,
    run_section_cycle,
)
from data.pipelines.rfp_intake.generators import generate_section  # noqa: E402


_META = {
    "client_name": "Sunset Bay Resorts",
    "location": "Florida",
    "service_type": "Co-branded concession",
    "scope": "3 resorts, 60–75k USD/año",
    "deadline": "15 November 2026",
    "budget_range": "USD 60,000 – 75,000 / año · COP 250–310M",
}

_ASPECTS = [
    "exclusividad en food court",
    "menú de autor",
    "co-branding signage",
]


def test_generator_marketing_includes_pillars_and_dual_currency():
    draft = generate_section("marketing", metadata=_META, key_aspects=_ASPECTS)
    lower = draft.lower()
    assert "calidad consistente" in lower
    assert "experiencia cálida" in lower
    assert "velocidad de servicio" in lower
    assert "cop" in lower and "usd" in lower
    assert "30 días" in lower
    assert "Sunset Bay Resorts" in draft


def test_evaluate_section_passes_compliant_draft():
    draft = generate_section("operaciones", metadata=_META, key_aspects=_ASPECTS)
    result = evaluate_section(
        department_id="operaciones",
        draft=draft,
        key_aspects=_ASPECTS,
        metadata=_META,
    )
    assert result["overall_pass"] is True
    assert result["readability"]["pass"] is True
    assert result["relevance"]["pass"] is True
    assert result["compliance"]["pass"] is True
    assert "feedback_for_generator" in result


def test_compliance_fails_on_setup_under_10_days():
    """Anclado a BRIEFING §5: montaje < 10 días hábiles → compliance.pass == false."""
    draft = generate_section(
        "operaciones",
        metadata=_META,
        key_aspects=_ASPECTS,
        force_violate="setup-min-10-days",
    )
    result = evaluate_compliance(draft, metadata=_META)
    assert result["pass"] is False
    assert "setup-min-10-days" in result["rule_ids"]
    assert result["violations"]


def test_compliance_fails_on_competitors():
    draft = generate_section(
        "marketing",
        metadata=_META,
        key_aspects=_ASPECTS,
        force_violate="no-competitors",
    )
    result = evaluate_compliance(draft, metadata=_META)
    assert result["pass"] is False
    assert "no-competitors" in result["rule_ids"]


def test_section_cycle_success():
    out = run_section_cycle(
        "procurement",
        metadata=_META,
        key_aspects=_ASPECTS,
        contact_name="Lucía Fernández",
        use_knowledge=False,
    )
    assert out["needs_human_review"] is False
    assert out["section_status"] == "aprobado_auto"
    assert (out.get("evaluation_results") or {}).get("overall_pass") is True
    assert out.get("draft_content")


def test_response_generation_orchestrates_departments():
    result = run_response_generation(
        ticket_id=42,
        metadata=_META,
        sections=[
            {
                "department_id": "marketing",
                "contact_name": "Camila Ospina",
                "key_aspects": _ASPECTS,
                "open_questions": [],
            },
            {
                "department_id": "operaciones",
                "contact_name": "Felipe Guerrero",
                "key_aspects": _ASPECTS,
                "open_questions": [],
            },
        ],
    )
    assert result["ticket_id"] == 42
    assert result["status"] in {"borrador_listo", "needs_human_review"}
    assert len(result["sections"]) == 2
    assert result["part3_handoff"]["ready"] is True
