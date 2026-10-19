#!/usr/bin/env python3
"""E2E reproducible Parte 1→2→3 con resumes programáticos (sin UI).

Uso:
  uv run python scripts/run_rfp_e2e_approval.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "services", _REPO / "services" / "api"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.pipelines.rfp_intake.approval_graph import (  # noqa: E402
    resume_department_approval,
    run_arbitration_and_maybe_finalize,
    start_department_approval,
)
from data.pipelines.rfp_intake.generation_graph import run_response_generation  # noqa: E402
from data.pipelines.rfp_intake.graph import run_rfp_intake  # noqa: E402


def main() -> int:
    seed = _REPO / "rfp-requests" / "brasaland" / "brasaland-request-2.md"
    part1 = run_rfp_intake(ticket_id=1, pdf_path=str(seed))
    assert part1["status"] == "analisis_completo", part1.get("status")
    print("Parte 1:", part1["status"], part1["metadata"].get("client_name"))

    sections = [
        {
            "department_id": r["department_id"],
            "contact_name": r.get("contact_name"),
            "key_aspects": r.get("key_aspects") or [],
            "open_questions": r.get("open_questions") or [],
        }
        for r in part1.get("worker_results") or []
    ]
    part2 = run_response_generation(
        ticket_id=1,
        metadata=part1.get("metadata") or {},
        sections=sections,
    )
    print("Parte 2:", part2["status"], "secciones=", len(part2["sections"]))

    approved_sections = []
    for sec in part2["sections"]:
        dept = sec["department_id"]
        start = start_department_approval(
            ticket_id=1,
            department_id=dept,
            draft_content=sec.get("draft_content") or "",
            key_aspects=sec.get("key_aspects") or [],
            approver_name=sec.get("contact_name"),
        )
        assert start["status"] == "interrupted"
        done = resume_department_approval(
            ticket_id=1, department_id=dept, action="approve", comment="OK E2E"
        )
        assert done["approval_status"] == "aprobado", done
        approved_sections.append(
            {
                **sec,
                "approval_status": "aprobado",
                "approver": done.get("approver_name") or sec.get("contact_name"),
            }
        )
        print(f"  aprobado {dept}")

    final = run_arbitration_and_maybe_finalize(
        ticket_id=1,
        metadata=part1.get("metadata") or {},
        sections=approved_sections,
        ceo_approval=None,
    )
    print("Parte 3:", final["status"])
    assert final["status"] == "terminado"
    assert final.get("final_document")
    print("--- Documento (extracto) ---")
    print((final["final_document"]["content"] or "")[:600])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
