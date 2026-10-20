"""Hub SSE in-process: fan-out de eventos RFP (+ opcionales) a suscriptores JWT.

Cada conexión es independiente (sin broker compartido entre procesos).
Buffer corto para reintento con Last-Event-ID tras desconexión.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import logging
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator

logger = logging.getLogger("api.rfp.sse")

# Eventos nombrados (nunca "message" genérico)
EVENT_RFP_TICKET_CREATED = "rfp_ticket_created"
EVENT_SALES_DROP_ALERT = "sales_drop_alert"

_REPLAY_MAX = 100


@dataclass
class SseEvent:
    id: int
    event: str
    data: dict[str, Any]
    created_at: str

    def encode(self) -> str:
        payload = json.dumps(self.data, ensure_ascii=False, default=str)
        return f"id: {self.id}\nevent: {self.event}\ndata: {payload}\n\n"


class RfpSseHub:
    """Pub/sub en memoria + buffer de replay."""

    def __init__(self, *, replay_max: int = _REPLAY_MAX) -> None:
        self._lock = threading.Lock()
        self._seq = itertools.count(1)
        self._replay: deque[SseEvent] = deque(maxlen=replay_max)
        self._subscribers: set[asyncio.Queue[SseEvent | None]] = set()

    def publish(self, event: str, data: dict[str, Any]) -> SseEvent:
        created = datetime.now(timezone.utc).isoformat()
        with self._lock:
            ev = SseEvent(
                id=next(self._seq),
                event=event,
                data=dict(data),
                created_at=created,
            )
            self._replay.append(ev)
            subs = list(self._subscribers)
        for q in subs:
            try:
                q.put_nowait(ev)
            except asyncio.QueueFull:
                logger.warning("sse subscriber queue full; dropping event id=%s", ev.id)
        logger.info("sse publish event=%s id=%s", event, ev.id)
        return ev

    def subscribe(self) -> asyncio.Queue[SseEvent | None]:
        q: asyncio.Queue[SseEvent | None] = asyncio.Queue(maxsize=64)
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[SseEvent | None]) -> None:
        with self._lock:
            self._subscribers.discard(q)

    def replay_since(self, last_event_id: int | None) -> list[SseEvent]:
        if last_event_id is None:
            return []
        with self._lock:
            return [e for e in self._replay if e.id > last_event_id]

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def reset_for_tests(self) -> None:
        """Vacía buffer y suscriptores (solo tests)."""
        with self._lock:
            self._seq = itertools.count(1)
            self._replay.clear()
            for q in list(self._subscribers):
                try:
                    q.put_nowait(None)
                except asyncio.QueueFull:
                    pass
            self._subscribers.clear()


_HUB = RfpSseHub()


def get_sse_hub() -> RfpSseHub:
    return _HUB


def reset_sse_hub_for_tests() -> None:
    get_sse_hub().reset_for_tests()


def publish_rfp_ticket_created(
    *,
    ticket_id: int,
    status: str,
    original_filename: str = "",
    client_name: str | None = None,
    location: str | None = None,
    service_type: str | None = None,
    scope: str | None = None,
    deadline: str | None = None,
    budget_range: str | None = None,
    departments_needed: list[str] | None = None,
    created_at: str | None = None,
) -> SseEvent:
    """Payload alineado al ticket RFP existente (estados ES del monorepo)."""
    data: dict[str, Any] = {
        "ticket_id": ticket_id,
        "status": status,  # analizando al registrarse
        "original_filename": original_filename,
        "client_name": client_name,
        "location": location,
        "service_type": service_type,
        "scope": scope,
        "deadline": deadline,
        "budget_range": budget_range,
        "departments_needed": departments_needed or [],
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "currency": "EUR",
        "currency_symbol": "€",
    }
    return get_sse_hub().publish(EVENT_RFP_TICKET_CREATED, data)


def publish_sales_drop_alert(
    *,
    country: str,
    drop_pct: float,
    week_label: str,
) -> SseEvent:
    """Caso opcional BRIEFING: caída de ventas >15% vs semana anterior."""
    data = {
        "country": country,
        "drop_pct": drop_pct,
        "threshold_pct": 15.0,
        "week_label": week_label,
        "notify": ["Mariana Restrepo", "Felipe Guerrero"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return get_sse_hub().publish(EVENT_SALES_DROP_ALERT, data)


async def stream_events(
    *,
    last_event_id: int | None = None,
    keepalive_seconds: float = 15.0,
) -> AsyncIterator[str]:
    hub = get_sse_hub()
    queue = hub.subscribe()
    try:
        # Replay corto de eventos perdidos
        for ev in hub.replay_since(last_event_id):
            yield ev.encode()
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=keepalive_seconds)
            except asyncio.TimeoutError:
                # Comentario keep-alive SSE
                yield ": keepalive\n\n"
                continue
            if item is None:
                break
            yield item.encode()
    finally:
        hub.unsubscribe(queue)
