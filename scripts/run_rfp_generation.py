#!/usr/bin/env python3
"""CLI Parte 2: genera/evalúa secciones desde un handoff sintético (sin HTTP).

Uso:
  uv run python scripts/run_rfp_generation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "services", _REPO / "services" / "api"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.pipelines.rfp_intake.generation_graph import run_response_generation  # noqa: E402
from data.pipelines.rfp_intake.generators import generate_section  # noqa: E402
from data.pipelines.rfp_intake.evaluators import evaluate_compliance  # noqa: E402


def main() -> int:
    meta = {
        "client_name": "Sunset Bay Resorts",
        "location": "Florida",
        "service_type": "Co-branded concession",
        "scope": "3 resorts",
        "deadline": "15 November 2026",
        "budget_range": "USD 60,000 – 75,000 / año · COP 250M",
    }
    aspects = ["exclusividad", "menú de autor", "co-branding"]
    ok = run_response_generation(
        ticket_id=0,
        metadata=meta,
        sections=[
            {"department_id": "marketing", "key_aspects": aspects, "open_questions": []},
            {"department_id": "operaciones", "key_aspects": aspects, "open_questions": []},
        ],
    )
    print("=== Ejemplo que aprueba ===")
    print("status=", ok["status"])
    for sec in ok["sections"]:
        ev = sec.get("evaluation_results") or {}
        print(
            f"  {sec['department_id']}: overall_pass={ev.get('overall_pass')} "
            f"needs_human_review={sec.get('needs_human_review')}"
        )

    bad = generate_section(
        "operaciones",
        metadata=meta,
        key_aspects=aspects,
        force_violate="setup-min-10-days",
    )
    comp = evaluate_compliance(bad, metadata=meta)
    print("\n=== Ejemplo que falla cumplimiento (setup < 10 días) ===")
    print(json.dumps(comp, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
