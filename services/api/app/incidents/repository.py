"""TinyDB persistence for centralized incidents."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.incidents.models import (
    ALLOWED_STATUS_TRANSITIONS,
    Incident,
    IncidentBranch,
    IncidentCategory,
    IncidentCreate,
    IncidentOrigin,
    IncidentStatus,
    IncidentSummary,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "incidents.json"


class IncidentRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(self.db_path)
        self._table = self._db.table("incidents")

    def close(self) -> None:
        self._db.close()

    def count(self) -> int:
        return len(self._table)

    def get(self, incident_id: int) -> Incident | None:
        doc = self._table.get(doc_id=incident_id)
        if doc is None:
            return None
        return self._to_incident(doc)

    def get_by_source_key(self, source_key: str) -> Incident | None:
        IncidentQ = Query()
        doc = self._table.get(IncidentQ.source_key == source_key)
        if doc is None:
            return None
        return self._to_incident(doc)

    def list(
        self,
        *,
        status: str | None = None,
        origin: str | None = None,
        branch: str | None = None,
        category: str | None = None,
    ) -> list[Incident]:
        docs = self._table.all()
        if status:
            docs = [d for d in docs if d.get("status") == status]
        if origin:
            docs = [d for d in docs if d.get("origin") == origin]
        if branch:
            docs = [d for d in docs if d.get("branch") == branch]
        if category:
            docs = [d for d in docs if d.get("category") == category]
        incidents = [self._to_incident(doc) for doc in docs]
        incidents.sort(key=lambda item: item.created_at, reverse=True)
        return incidents

    def create(
        self,
        payload: IncidentCreate,
        *,
        status: IncidentStatus = IncidentStatus.OPEN,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        source_key: str | None = None,
    ) -> Incident:
        now = datetime.now(timezone.utc)
        created = created_at or now
        updated = updated_at or created
        data: dict[str, Any] = {
            "title": payload.title.strip(),
            "description": payload.description.strip(),
            "category": payload.category.value,
            "status": status.value,
            "origin": payload.origin.value,
            "branch": payload.branch.value,
            "created_at": created.astimezone(timezone.utc).isoformat(),
            "updated_at": updated.astimezone(timezone.utc).isoformat(),
            "source_key": source_key,
        }
        doc_id = self._table.insert(data)
        return self.get(doc_id)  # type: ignore[return-value]

    def update_status(
        self, incident_id: int, new_status: IncidentStatus
    ) -> Incident | None:
        current = self.get(incident_id)
        if current is None:
            return None
        allowed = ALLOWED_STATUS_TRANSITIONS[current.status]
        if new_status not in allowed:
            raise ValueError(
                f"Transición no permitida: {current.status.value} → {new_status.value}"
            )
        now = datetime.now(timezone.utc)
        self._table.update(
            {"status": new_status.value, "updated_at": now.isoformat()},
            doc_ids=[incident_id],
        )
        return self.get(incident_id)

    def summary(self) -> IncidentSummary:
        docs = self._table.all()
        by_status = Counter(d.get("status") or "unknown" for d in docs)
        by_category = Counter(d.get("category") or "unknown" for d in docs)
        by_origin = Counter(d.get("origin") or "unknown" for d in docs)
        by_branch = Counter(d.get("branch") or "unknown" for d in docs)
        # Ensure known keys exist with 0 when empty DB
        for status in IncidentStatus:
            by_status.setdefault(status.value, 0)
        for category in IncidentCategory:
            by_category.setdefault(category.value, 0)
        for origin in IncidentOrigin:
            by_origin.setdefault(origin.value, 0)
        for branch in IncidentBranch:
            by_branch.setdefault(branch.value, 0)
        return IncidentSummary(
            total=len(docs),
            by_status=dict(sorted(by_status.items())),
            by_category=dict(sorted(by_category.items())),
            by_origin=dict(sorted(by_origin.items())),
            by_branch=dict(sorted(by_branch.items())),
        )

    @staticmethod
    def _to_incident(doc: dict[str, Any]) -> Incident:
        payload = dict(doc)
        payload["id"] = doc.doc_id  # type: ignore[attr-defined]
        payload.pop("source_key", None)
        for key in ("created_at", "updated_at"):
            raw = payload.get(key)
            if isinstance(raw, str):
                payload[key] = datetime.fromisoformat(raw)
        return Incident.model_validate(payload)
