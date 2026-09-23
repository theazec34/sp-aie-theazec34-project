"""Support-ticket lookup tool — reads the real Incident manager (GET only).

Auth: ``GET /api/incidents`` is public in this monorepo (no JWT). When calling
in-process we use ``IncidentRepository`` (same TinyDB store as the API).
"""

from __future__ import annotations

import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path

from agent.tools.contracts import (
    TicketLookupInput,
    TicketLookupOutput,
    TicketRecord,
)

logger = logging.getLogger("agent.tools.incidents")

DEFAULT_TIMEOUT_S = float(os.getenv("AGENT_TOOL_TIMEOUT_S", "4"))

_API = Path(__file__).resolve().parents[2] / "api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))


def _fetch_tickets(payload: TicketLookupInput) -> TicketLookupOutput:
    from app.incidents.repository import IncidentRepository

    repo = IncidentRepository()
    try:
        if payload.ticket_id is not None:
            item = repo.get(payload.ticket_id)
            if item is None:
                return TicketLookupOutput(
                    ok=False,
                    error=f"Incidencia {payload.ticket_id} no encontrada",
                )
            return TicketLookupOutput(
                ok=True,
                tickets=[TicketRecord.model_validate(item.model_dump())],
            )

        items = repo.list(
            status=payload.status,
            origin=payload.origin,
            branch=payload.branch,
            category=payload.category,
        )
        trimmed = items[: payload.limit]
        return TicketLookupOutput(
            ok=True,
            tickets=[TicketRecord.model_validate(i.model_dump()) for i in trimmed],
        )
    finally:
        repo.close()


def lookup_support_ticket(
    payload: TicketLookupInput,
    *,
    timeout_s: float | None = None,
) -> TicketLookupOutput:
    """Read-only ticket lookup with explicit timeout and honest errors."""
    limit = timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_fetch_tickets, payload)
            return future.result(timeout=limit)
    except FuturesTimeout:
        logger.warning("ticket tool timed out after %ss", limit)
        return TicketLookupOutput(
            ok=False,
            timed_out=True,
            error=f"Timeout ({limit}s) al consultar el gestor de incidencias",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("ticket tool failed")
        return TicketLookupOutput(
            ok=False,
            error=f"No se pudo consultar incidencias: {type(exc).__name__}",
        )
