"""Arbitraje determinista BRIEFING §7 — árbitro fijo, no consenso LLM."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from data.pipelines.rfp_intake.guidelines import (
    ARBITRATION_TRIGGERS,
    CEO_THRESHOLD_EUR,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect_conflicts(
    *,
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
    ceo_approved: bool = False,
) -> list[dict[str, Any]]:
    """Detecta triggers en estado estructurado (no texto libre)."""
    found: list[dict[str, Any]] = []
    drafts = {
        s.get("department_id"): (s.get("draft_content") or "").lower() for s in sections
    }
    ops = drafts.get("operaciones", "")
    proc = drafts.get("procurement", "")

    # setup-sla-breach: cualquier sección promete < 10 días hábiles
    for dept, text in drafts.items():
        for m in re.finditer(r"(\d+)\s*días\s*hábiles", text):
            if int(m.group(1)) < 10:
                trig = ARBITRATION_TRIGGERS["setup-sla-breach"]
                found.append(
                    {
                        "trigger_id": "setup-sla-breach",
                        "arbiter": trig["arbiter"],
                        "department_id": trig["department_id"],
                        "evidence": {"department_id": dept, "days": int(m.group(1))},
                        "resolution": trig["rule"],
                        "action": "request_changes",
                        "targets": [dept],
                    }
                )
                break

    # cost-vs-feasibility: señal estructurada si procurement marca costo insuficiente
    # o si operaciones menciona precio por cubierto y procurement "no soporta"
    if "no soporta" in proc or "insuficiente" in proc:
        if "precio" in ops or "cubierto" in ops or "por evento" in ops:
            trig = ARBITRATION_TRIGGERS["cost-vs-feasibility"]
            found.append(
                {
                    "trigger_id": "cost-vs-feasibility",
                    "arbiter": trig["arbiter"],
                    "department_id": trig["department_id"],
                    "evidence": {"operaciones": True, "procurement": True},
                    "resolution": trig["rule"],
                    "action": "request_changes",
                    "targets": ["operaciones", "procurement"],
                }
            )

    # ceo-threshold
    budget = str(metadata.get("budget_range") or "")
    over = _annual_over_threshold(budget, sections)
    if over and not ceo_approved:
        trig = ARBITRATION_TRIGGERS["ceo-threshold"]
        found.append(
            {
                "trigger_id": "ceo-threshold",
                "arbiter": trig["arbiter"],
                "department_id": "ceo",
                "evidence": {"budget_range": budget, "threshold_eur": CEO_THRESHOLD_EUR},
                "resolution": trig["rule"],
                "action": "await_ceo",
                "targets": ["ceo"],
            }
        )

    # Dedup by trigger_id
    seen: set[str] = set()
    uniq: list[dict[str, Any]] = []
    for item in found:
        tid = item["trigger_id"]
        if tid in seen:
            continue
        seen.add(tid)
        uniq.append(item)
    return uniq


def apply_arbitration(conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    """Resuelve con árbitro fijo; devuelve órdenes estructuradas."""
    orders: list[dict[str, Any]] = []
    for c in conflicts:
        orders.append(
            {
                "trigger_id": c["trigger_id"],
                "arbiter": c["arbiter"],
                "action": c["action"],
                "targets": c.get("targets") or [],
                "resolution": c["resolution"],
                "decided_at": _now_iso(),
                "method": "fixed_arbiter",  # nunca LLM freestyle
            }
        )
    return {
        "conflicts": conflicts,
        "orders": orders,
        "blocked_synthesis": any(o["action"] == "await_ceo" for o in orders),
        "request_changes_targets": sorted(
            {
                t
                for o in orders
                if o["action"] == "request_changes"
                for t in o["targets"]
            }
        ),
    }


def _annual_over_threshold(budget: str, sections: list[dict[str, Any]]) -> bool:
    text = budget + " " + " ".join(s.get("draft_content") or "" for s in sections)
    if re.search(r"50[.,]?000\s*€|>\s*50[.,]?000", text):
        return True
    if re.search(r"6[0-9]\s*[–\-]\s*75\s*k|60[,.]?000|75[,.]?000", text, re.I):
        return True
    m = re.search(r"(\d[\d.]*)\s*k\s*€", text, re.I)
    if m:
        try:
            return float(m.group(1)) * 1000 > CEO_THRESHOLD_EUR
        except ValueError:
            return False
    return False
