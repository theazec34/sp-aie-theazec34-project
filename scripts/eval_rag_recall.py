"""Compute Recall@3 for Brasaland RAG retrieval eval set.

Usage (from repo root):

    PYTHONPATH=. uv run python scripts/eval_rag_recall.py
    # or
    uv run python -m scripts.eval_rag_recall
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# Re-bind cwd-independent imports after path fix
from data.pipelines.rag import retrieve  # noqa: E402
from data.process.rag import setup  # noqa: E402

EVAL_PATH = _REPO / "data" / "eval" / "test-queries.json"


def main() -> int:
    setup()
    cases = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    hits = 0
    rows = []
    for case in cases:
        results = retrieve(case["question"], k=3, min_score=0.0)
        sources = [r.get("source_document") for r in results]
        expected = case["expected_source_document"]
        ok = expected in sources
        hits += int(ok)
        rows.append(
            {
                "id": case["id"],
                "ok": ok,
                "expected": expected,
                "top3": sources,
            }
        )
    total = len(cases)
    recall = hits / total if total else 0.0
    report = {
        "metric": "Recall@3",
        "hits": hits,
        "total": total,
        "recall_at_3": round(recall, 4),
        "pass": recall >= 0.8,
        "cases": rows,
    }
    out = _REPO / "data" / "eval" / "rag_recall_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
