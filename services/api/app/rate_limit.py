"""Rate limiting in-process (NIST Protect — control de costo / abuso en endpoints LLM).

Sin dependencia nueva: ventana deslizante por clave (user_id o IP).
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Máximo `max_calls` en `window_seconds` por clave."""

    def __init__(self, *, max_calls: int, window_seconds: float) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.max_calls:
                return False
            q.append(now)
            return True

    def reset_for_tests(self) -> None:
        with self._lock:
            self._hits.clear()


# Defaults: 20 consultas al modelo / minuto / usuario (ajustable por env)
_AGENT_MAX = int(os.getenv("AGENT_RATE_LIMIT_MAX", "20"))
_AGENT_WINDOW = float(os.getenv("AGENT_RATE_LIMIT_WINDOW_SECONDS", "60"))
_KNOWLEDGE_MAX = int(os.getenv("KNOWLEDGE_RATE_LIMIT_MAX", "30"))
_KNOWLEDGE_WINDOW = float(os.getenv("KNOWLEDGE_RATE_LIMIT_WINDOW_SECONDS", "60"))

agent_query_limiter = SlidingWindowRateLimiter(
    max_calls=_AGENT_MAX, window_seconds=_AGENT_WINDOW
)
knowledge_query_limiter = SlidingWindowRateLimiter(
    max_calls=_KNOWLEDGE_MAX, window_seconds=_KNOWLEDGE_WINDOW
)


def enforce_rate_limit(limiter: SlidingWindowRateLimiter, key: str, *, detail: str) -> None:
    if not limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(int(limiter.window_seconds))},
        )


def client_key(request: Request, user_id: str | int | None) -> str:
    if user_id is not None:
        return f"user:{user_id}"
    client = request.client.host if request.client else "unknown"
    return f"ip:{client}"
