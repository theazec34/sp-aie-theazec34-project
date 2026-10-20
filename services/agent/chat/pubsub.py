"""Pub/Sub in-process: canal `chat.<session_id>` — productor ≠ consumidores WS."""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import defaultdict
from typing import Any

logger = logging.getLogger("agent.chat.pubsub")


class ChatPubSub:
    """Fan-out por sesión. Varios WS en la misma sesión reciben el mismo evento
    sin volver a invocar al agente (un solo productor por generation_id).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: dict[str, set[asyncio.Queue[dict[str, Any] | None]]] = defaultdict(set)

    @staticmethod
    def channel(session_id: str) -> str:
        return f"chat.{session_id}"

    def subscribe(self, session_id: str) -> asyncio.Queue[dict[str, Any] | None]:
        q: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue(maxsize=256)
        key = self.channel(session_id)
        with self._lock:
            self._subs[key].add(q)
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue[dict[str, Any] | None]) -> None:
        key = self.channel(session_id)
        with self._lock:
            self._subs[key].discard(q)
            if not self._subs[key]:
                del self._subs[key]

    def publish(self, session_id: str, event: str, data: dict[str, Any]) -> None:
        payload = {"event": event, "data": data}
        key = self.channel(session_id)
        with self._lock:
            queues = list(self._subs.get(key, ()))
        for q in queues:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("chat pubsub queue full session=%s event=%s", session_id, event)

    def subscriber_count(self, session_id: str) -> int:
        key = self.channel(session_id)
        with self._lock:
            return len(self._subs.get(key, ()))

    def reset_for_tests(self) -> None:
        with self._lock:
            for qs in self._subs.values():
                for q in list(qs):
                    try:
                        q.put_nowait(None)
                    except asyncio.QueueFull:
                        pass
            self._subs.clear()


_BUS = ChatPubSub()


def get_chat_pubsub() -> ChatPubSub:
    return _BUS
