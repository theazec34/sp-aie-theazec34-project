#!/usr/bin/env python3
"""CLI smoke runner for the rfp_intake LangGraph (no HTTP).

Usage:
  uv run python scripts/run_rfp_intake.py rfp-requests/brasaland/brasaland-request-1.pdf
  uv run python scripts/run_rfp_intake.py rfp-requests/brasaland/brasaland-request-3.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "services", _REPO / "services" / "api"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from data.pipelines.rfp_intake.graph import run_rfp_intake  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run rfp_intake pipeline on a PDF/MD")
    parser.add_argument("path", type=Path, help="Path to PDF or Markdown fixture")
    parser.add_argument("--ticket-id", type=int, default=0, help="Synthetic ticket id")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")
    args = parser.parse_args()
    path = args.path if args.path.is_absolute() else _REPO / args.path
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 1

    result = run_rfp_intake(ticket_id=args.ticket_id, pdf_path=str(path))
    if args.json:
        # Drop huge markdown for readability
        slim = {k: v for k, v in result.items() if k != "markdown"}
        print(json.dumps(slim, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"status={result.get('status')}")
        print(f"discard_reason={result.get('discard_reason')}")
        meta = result.get("metadata") or {}
        print(
            f"client={meta.get('client_name')} departments={meta.get('departments_needed')}"
        )
        synth = result.get("synthesizer") or {}
        for line in synth.get("summary_lines") or []:
            print(f"  {line}")
        for dept in synth.get("departments") or []:
            print(f"  → {dept.get('department_id')} / {dept.get('contact')}")
            for aspect in (dept.get("ask_them") or [])[:5]:
                print(f"      - {aspect}")
    return 0 if result.get("status") in {"analisis_completo", "descartado"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
