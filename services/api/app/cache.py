"""In-process TTL cache for FastAPI read endpoints.

Not for private/session data with a shared key — callers must scope keys
when the payload is user-specific. Values are deep-copied on get/set so
callers cannot mutate cache entries by accident.
"""

from __future__ import annotations

import copy
import threading
import time
from typing import Any


class TtlCache:
    """Thread-safe dict cache with per-entry TTL and prefix invalidation."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None
            expires_at, value = entry
            if expires_at <= now:
                del self._store[key]
                self.misses += 1
                return None
            self.hits += 1
            return copy.deepcopy(value)

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        if ttl_seconds <= 0:
            return
        expires_at = time.monotonic() + ttl_seconds
        with self._lock:
            self._store[key] = (expires_at, copy.deepcopy(value))

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in [k for k in self._store if k.startswith(prefix)]:
                del self._store[key]

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "entries": len(self._store),
                "hits": self.hits,
                "misses": self.misses,
            }


# Process-wide caches (separate namespaces keep invalidation simple).
incidents_cache = TtlCache()
suppliers_cache = TtlCache()
telemetry_report_cache = TtlCache()

# TTL choices documented in CACHING_REPORT.md
INCIDENTS_SUMMARY_TTL = 30.0  # seconds — dashboard aggregates; writes invalidate
SUPPLIERS_LIST_TTL = 60.0  # seconds — directory changes rarely
TELEMETRY_REPORT_TTL = 60.0  # seconds — report pipeline; key = start_date|end_date
