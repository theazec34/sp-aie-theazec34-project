"""Tests Parte 3: interrupt/resume, paralelismo, arbitraje, límite."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
for _p in (_REPO, _REPO / "services", _REPO / "services" / "api"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.pipelines.rfp_intake.arbitration import (  # noqa: E402
    apply_arbitration,
    detect_conflicts,
)
from data.pipelines.rfp_intake.approval_graph import (  # noqa: E402
    resume_department_approval,
    run_arbitration_and_maybe_finalize,
    start_department_approval,
    thread_id_for,
)
from data.pipelines.rfp_intake.generators import generate_section  # noqa: E402
from data.pipelines.rfp_intake.guidelines import MAX_APPROVAL_ITERATIONS  # noqa: E402

_META = {
    "client_name": "Andes Tech Solutions",
    "location": "Medellín",
    "service_type": "Catering corporativo",
    "scope": "220 empleados, 12 meses",
    "budget_range": "40.000 €/año",
    "deadline": "30 octubre 2026",
}
_ASPECTS = ["catering semanal", "menú estándar"]


def _draft(dept: str) -> str:
    return generate_section(dept, metadata=_META, key_aspects=_ASPECTS)


def test_thread_id_namespaced():
    assert thread_id_for(12, "marketing") == "rfp-12:marketing"
    assert thread_id_for(12, "ceo") == "rfp-12:ceo"


def test_interrupt_and_resume_approve():
    draft = _draft("marketing")
    start = start_department_approval(
        ticket_id=9101,
        department_id="marketing",
        draft_content=draft,
        key_aspects=_ASPECTS,
    )
    assert start["status"] == "interrupted"
    assert start["pending_interrupt"]
    done = resume_department_approval(
        ticket_id=9101, department_id="marketing", action="approve"
    )
    assert done["status"] == "completed"
    assert done["approval_status"] == "aprobado"
    assert done["trace"]


def test_parallel_branches_non_blocking():
    """Depto B puede aprobarse mientras A sigue interrupted."""
    tid = 9102
    a = start_department_approval(
        ticket_id=tid,
        department_id="marketing",
        draft_content=_draft("marketing"),
        key_aspects=_ASPECTS,
    )
    b = start_department_approval(
        ticket_id=tid,
        department_id="operaciones",
        draft_content=_draft("operaciones"),
        key_aspects=_ASPECTS,
    )
    assert a["status"] == "interrupted"
    assert b["status"] == "interrupted"
    b_done = resume_department_approval(
        ticket_id=tid, department_id="operaciones", action="approve"
    )
    assert b_done["approval_status"] == "aprobado"
    # marketing sigue independiente (aún interrupted hasta resume)
    a2 = resume_department_approval(
        ticket_id=tid, department_id="marketing", action="approve"
    )
    assert a2["approval_status"] == "aprobado"


def test_arbitration_setup_sla_breach():
    sections = [
        {
            "department_id": "operaciones",
            "draft_content": "Montaje en 5 días hábiles garantizado. € 10.000",
            "approval_status": "aprobado",
        }
    ]
    conflicts = detect_conflicts(metadata=_META, sections=sections)
    assert any(c["trigger_id"] == "setup-sla-breach" for c in conflicts)
    arb = apply_arbitration(conflicts)
    assert arb["orders"]
    assert arb["orders"][0]["method"] == "fixed_arbiter"
    assert arb["orders"][0]["arbiter"] == "Felipe Guerrero"


def test_arbitration_ceo_threshold():
    meta = {**_META, "budget_range": "60.000 – 75.000 €/año"}
    sections = [
        {
            "department_id": "marketing",
            "draft_content": _draft("marketing"),
            "approval_status": "aprobado",
        }
    ]
    conflicts = detect_conflicts(metadata=meta, sections=sections, ceo_approved=False)
    assert any(c["trigger_id"] == "ceo-threshold" for c in conflicts)


def test_finalize_after_all_approvals():
    sections = [
        {
            "department_id": "marketing",
            "draft_content": _draft("marketing"),
            "approval_status": "aprobado",
            "approver": "Camila Ospina",
        },
        {
            "department_id": "operaciones",
            "draft_content": _draft("operaciones"),
            "approval_status": "aprobado",
            "approver": "Felipe Guerrero",
        },
        {
            "department_id": "procurement",
            "draft_content": _draft("procurement"),
            "approval_status": "aprobado",
            "approver": "Lucía Fernández",
        },
    ]
    out = run_arbitration_and_maybe_finalize(
        ticket_id=9103, metadata=_META, sections=sections, ceo_approval=None
    )
    assert out["status"] == "terminado"
    assert out["final_document"]
    assert "€" in out["final_document"]["content"] or out["final_document"]["currency"] == "EUR"


def test_max_approval_iterations_constant():
    assert MAX_APPROVAL_ITERATIONS >= 2
