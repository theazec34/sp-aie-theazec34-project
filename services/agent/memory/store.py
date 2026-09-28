"""Persistent episodic memory store — Redis or JSON file.

NEVER writes to Qdrant RAG collections (`brasaland_knowledge` / `*_knowledge`).
Namespace: ``brasaland_agent_memory``.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Protocol

from agent.memory.models import MemoryCategory, MemoryEntry

logger = logging.getLogger("agent.memory.store")

MEMORY_NAMESPACE = "brasaland_agent_memory"
# Hard cap — consolidation + eviction keep growth bounded.
MAX_ENTRIES = int(os.getenv("AGENT_MEMORY_MAX_ENTRIES", "200"))
TTL_DAYS = int(os.getenv("AGENT_MEMORY_TTL_DAYS", "90"))
RAG_FORBIDDEN_COLLECTIONS = frozenset(
    {
        "brasaland_knowledge",
        "company_knowledge",
        "knowledge",
    }
)


class MemoryStore(Protocol):
    def read(
        self,
        *,
        location: str | None = None,
        category: MemoryCategory | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]: ...

    def write(self, entry: MemoryEntry) -> MemoryEntry: ...

    def delete(self, entry_id: str) -> bool: ...

    def list_all(self) -> list[MemoryEntry]: ...

    def consolidate(self) -> int: ...

    def cleanup(self) -> dict[str, int]: ...


def _assert_not_rag(collection_or_ns: str) -> None:
    key = collection_or_ns.strip().lower()
    if key in RAG_FORBIDDEN_COLLECTIONS or key.endswith("_knowledge"):
        raise RuntimeError(
            f"Refusing to write agent memory into RAG collection '{collection_or_ns}'. "
            f"Use namespace '{MEMORY_NAMESPACE}' only."
        )


class FileMemoryStore:
    """JSON-file episodic store (tests / offline). Explicit R/W interface."""

    def __init__(self, path: Path | None = None) -> None:
        _assert_not_rag(MEMORY_NAMESPACE)
        if path is None:
            raw = os.getenv("AGENT_MEMORY_DIR", "data/eval/agent_memory")
            path = Path(raw)
            if not path.is_absolute():
                path = Path(__file__).resolve().parents[3] / path
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self._file = self.path / "entries.json"
        self._lock = Lock()

    def _load(self) -> list[MemoryEntry]:
        if not self._file.exists():
            return []
        data = json.loads(self._file.read_text(encoding="utf-8"))
        return [MemoryEntry.model_validate(row) for row in data.get("entries", [])]

    def _save(self, entries: list[MemoryEntry]) -> None:
        payload = {
            "namespace": MEMORY_NAMESPACE,
            "not_rag": True,
            "entries": [e.model_dump(mode="json") for e in entries],
        }
        self._file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_all(self) -> list[MemoryEntry]:
        with self._lock:
            return self._load()

    def read(
        self,
        *,
        location: str | None = None,
        category: MemoryCategory | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        entries = self.list_all()
        if location:
            loc = location.lower()
            entries = [e for e in entries if (e.location or "").lower() == loc]
        if category:
            entries = [e for e in entries if e.category == category]
        entries.sort(key=lambda e: (e.relevance, e.updated_at), reverse=True)
        return entries[:limit]

    def write(self, entry: MemoryEntry) -> MemoryEntry:
        _assert_not_rag(MEMORY_NAMESPACE)
        with self._lock:
            entries = self._load()
            # Dedup: same location+category+normalized fact → update
            norm = entry.fact.strip().lower()
            replaced = False
            for i, existing in enumerate(entries):
                same_loc = (existing.location or "") == (entry.location or "")
                same_cat = existing.category == entry.category
                if same_loc and same_cat and existing.fact.strip().lower() == norm:
                    entry.entry_id = existing.entry_id
                    entry.created_at = existing.created_at
                    entry.updated_at = datetime.now(timezone.utc)
                    entries[i] = entry
                    replaced = True
                    break
            if not replaced:
                entries.append(entry)
            self._save(entries)
        self.cleanup()
        return entry

    def delete(self, entry_id: str) -> bool:
        with self._lock:
            entries = self._load()
            new = [e for e in entries if e.entry_id != entry_id]
            if len(new) == len(entries):
                return False
            self._save(new)
            return True

    def consolidate(self) -> int:
        """Merge entries sharing location+category into one summary fact."""
        with self._lock:
            entries = self._load()
            groups: dict[tuple[str, str], list[MemoryEntry]] = {}
            for e in entries:
                key = ((e.location or "global").lower(), e.category.value)
                groups.setdefault(key, []).append(e)

            merged: list[MemoryEntry] = []
            removed = 0
            for (loc, cat), group in groups.items():
                if len(group) <= 1:
                    merged.extend(group)
                    continue
                group.sort(key=lambda x: x.updated_at)
                facts = []
                seen: set[str] = set()
                for g in group:
                    n = g.fact.strip()
                    k = n.lower()
                    if k in seen:
                        continue
                    seen.add(k)
                    facts.append(n)
                summary = f"[{loc}/{cat}] " + " | ".join(facts[-5:])
                keep = group[-1].model_copy(
                    update={
                        "fact": summary,
                        "consolidated": True,
                        "updated_at": datetime.now(timezone.utc),
                        "relevance": max(g.relevance for g in group),
                    }
                )
                merged.append(keep)
                removed += len(group) - 1
            self._save(merged)
            logger.info("memory consolidate removed=%s remaining=%s", removed, len(merged))
            return removed

    def cleanup(self) -> dict[str, int]:
        """TTL expiry + hard cap + soft consolidate when over soft limit."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=TTL_DAYS)
        with self._lock:
            entries = self._load()
            before = len(entries)
            kept = [
                e
                for e in entries
                if (e.updated_at if e.updated_at.tzinfo else e.updated_at.replace(tzinfo=timezone.utc))
                >= cutoff
            ]
            expired = before - len(kept)
            kept.sort(key=lambda e: (e.relevance, e.updated_at), reverse=True)
            trimmed = 0
            if len(kept) > MAX_ENTRIES:
                trimmed = len(kept) - MAX_ENTRIES
                kept = kept[:MAX_ENTRIES]
            self._save(kept)
        # Soft consolidate when approaching cap
        consolidated = 0
        if len(kept) > MAX_ENTRIES * 0.8:
            consolidated = self.consolidate()
        return {"expired": expired, "trimmed": trimmed, "consolidated": consolidated}


class RedisMemoryStore:
    """Redis hash/list backend under key prefix brasaland_agent_memory:*."""

    def __init__(self, redis_url: str | None = None) -> None:
        import redis

        _assert_not_rag(MEMORY_NAMESPACE)
        url = redis_url or os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
        self._r = redis.Redis.from_url(url, decode_responses=True)
        self._key = f"{MEMORY_NAMESPACE}:entries"

    def list_all(self) -> list[MemoryEntry]:
        raw = self._r.hgetall(self._key)
        return [MemoryEntry.model_validate_json(v) for v in raw.values()]

    def read(
        self,
        *,
        location: str | None = None,
        category: MemoryCategory | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        entries = self.list_all()
        if location:
            loc = location.lower()
            entries = [e for e in entries if (e.location or "").lower() == loc]
        if category:
            entries = [e for e in entries if e.category == category]
        entries.sort(key=lambda e: (e.relevance, e.updated_at), reverse=True)
        return entries[:limit]

    def write(self, entry: MemoryEntry) -> MemoryEntry:
        _assert_not_rag(MEMORY_NAMESPACE)
        # Dedup scan
        for existing in self.list_all():
            if (
                (existing.location or "") == (entry.location or "")
                and existing.category == entry.category
                and existing.fact.strip().lower() == entry.fact.strip().lower()
            ):
                entry.entry_id = existing.entry_id
                entry.created_at = existing.created_at
                break
        entry.updated_at = datetime.now(timezone.utc)
        self._r.hset(self._key, entry.entry_id, entry.model_dump_json())
        self.cleanup()
        return entry

    def delete(self, entry_id: str) -> bool:
        return bool(self._r.hdel(self._key, entry_id))

    def consolidate(self) -> int:
        file_like = FileMemoryStore.__new__(FileMemoryStore)
        # Reuse consolidate logic via temporary file snapshot
        tmp = FileMemoryStore(
            path=Path(os.getenv("AGENT_MEMORY_DIR", "data/eval/agent_memory")) / "_redis_tmp"
        )
        tmp._save(self.list_all())  # noqa: SLF001
        removed = tmp.consolidate()
        self._r.delete(self._key)
        for e in tmp.list_all():
            self._r.hset(self._key, e.entry_id, e.model_dump_json())
        return removed

    def cleanup(self) -> dict[str, int]:
        tmp = FileMemoryStore(
            path=Path(os.getenv("AGENT_MEMORY_DIR", "data/eval/agent_memory")) / "_redis_tmp"
        )
        tmp._save(self.list_all())  # noqa: SLF001
        stats = tmp.cleanup()
        self._r.delete(self._key)
        for e in tmp.list_all():
            self._r.hset(self._key, e.entry_id, e.model_dump_json())
        return stats


_STORE: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    """Factory: Redis when AGENT_MEMORY_BACKEND=redis, else file."""
    global _STORE
    if _STORE is not None:
        return _STORE
    backend = os.getenv("AGENT_MEMORY_BACKEND", "file").strip().lower()
    if backend == "redis":
        try:
            store = RedisMemoryStore()
            store._r.ping()  # noqa: SLF001
            _STORE = store
            return _STORE
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis memory unavailable (%s); falling back to file", exc)
    _STORE = FileMemoryStore()
    return _STORE


def reset_memory_store_for_tests() -> None:
    global _STORE
    _STORE = None
