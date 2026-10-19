"""Track multi-turn sensitive probes (e.g. gradual recipe extraction)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from threading import Lock

_LOCK = Lock()

_RECIPE_HINT = re.compile(
    r"\b(receta|recipe|salsa\s+de\s+la\s+casa|house\s+sauce|f[oó]rmula|"
    r"ingrediente|ingredient|proporci[oó]n|cantidad\s+exacta|mother\s+recipe|"
    r"receta\s+madre)\b",
    re.I,
)
_PRICE_HINT = re.compile(
    r"\b(costo\s+por\s+porci[oó]n|cost\s+per\s+portion|precio\s+negociado|"
    r"contract\s+price|lo\s+que\s+le\s+cobramos|supplier\s+cost)\b",
    re.I,
)


def _path() -> Path:
    raw = os.getenv("AGENT_GUARDRAIL_LOG_DIR", "data/eval/agent_guardrails")
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    path.mkdir(parents=True, exist_ok=True)
    return path / "session_probes.json"


def note_message(session_id: str, text: str) -> dict[str, int]:
    """Record probe signals for this session; return cumulative counts."""
    recipe = 1 if _RECIPE_HINT.search(text or "") else 0
    price = 1 if _PRICE_HINT.search(text or "") else 0
    with _LOCK:
        data = _load()
        row = data.get(session_id) or {"recipe_probes": 0, "price_probes": 0, "messages": 0}
        row["recipe_probes"] = int(row["recipe_probes"]) + recipe
        row["price_probes"] = int(row["price_probes"]) + price
        row["messages"] = int(row["messages"]) + 1
        data[session_id] = row
        _save(data)
        return {
            "recipe_probes": int(row["recipe_probes"]),
            "price_probes": int(row["price_probes"]),
            "messages": int(row["messages"]),
        }


def get_counts(session_id: str) -> dict[str, int]:
    with _LOCK:
        data = _load()
        row = data.get(session_id) or {}
        return {
            "recipe_probes": int(row.get("recipe_probes", 0)),
            "price_probes": int(row.get("price_probes", 0)),
            "messages": int(row.get("messages", 0)),
        }


def clear_session(session_id: str) -> None:
    with _LOCK:
        data = _load()
        data.pop(session_id, None)
        _save(data)


def _load() -> dict:
    p = _path()
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    _path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
