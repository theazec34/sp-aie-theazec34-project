"""TinyDB persistence for public website intake."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import TinyDB

from app.public_intake.models import (
    CareerCreate,
    CareerPublic,
    ReservationCreate,
    ReservationPublic,
    ReservationStatus,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "public_intake.json"


class PublicIntakeRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(self.db_path)
        self._reservations = self._db.table("reservations")
        self._careers = self._db.table("careers")

    def close(self) -> None:
        self._db.close()

    def create_reservation(self, payload: ReservationCreate) -> ReservationPublic:
        now = datetime.now(timezone.utc)
        data = {
            "full_name": payload.full_name,
            "phone": payload.phone,
            "email": str(payload.email).lower(),
            "date": payload.date.isoformat(),
            "time": payload.time.isoformat(timespec="minutes"),
            "guests": payload.guests,
            "notes": payload.notes,
            "status": ReservationStatus.RECEIVED.value,
            "created_at": now.isoformat(),
        }
        doc_id = self._reservations.insert(data)
        return self.get_reservation(doc_id)  # type: ignore[return-value]

    def list_reservations(self) -> list[ReservationPublic]:
        docs = sorted(
            self._reservations.all(),
            key=lambda d: d.get("created_at") or "",
            reverse=True,
        )
        return [self._to_reservation(d) for d in docs]

    def get_reservation(self, reservation_id: int) -> ReservationPublic | None:
        doc = self._reservations.get(doc_id=reservation_id)
        if doc is None:
            return None
        return self._to_reservation(doc)

    def create_career(self, payload: CareerCreate) -> CareerPublic:
        now = datetime.now(timezone.utc)
        data = {
            "name": payload.name.strip(),
            "email": str(payload.email).lower(),
            "phone": payload.phone.strip(),
            "department": payload.department.strip(),
            "experience_years": payload.experience_years,
            "message": payload.message.strip(),
            "cv_filename": (payload.cv_filename or "").strip(),
            "privacy_accepted": True,
            "created_at": now.isoformat(),
        }
        doc_id = self._careers.insert(data)
        return self.get_career(doc_id)  # type: ignore[return-value]

    def list_careers(self) -> list[CareerPublic]:
        docs = sorted(
            self._careers.all(),
            key=lambda d: d.get("created_at") or "",
            reverse=True,
        )
        return [self._to_career(d) for d in docs]

    def get_career(self, career_id: int) -> CareerPublic | None:
        doc = self._careers.get(doc_id=career_id)
        if doc is None:
            return None
        return self._to_career(doc)

    @staticmethod
    def _to_reservation(doc: dict[str, Any]) -> ReservationPublic:
        payload = dict(doc)
        payload["id"] = doc.doc_id  # type: ignore[attr-defined]
        return ReservationPublic.model_validate(payload)

    @staticmethod
    def _to_career(doc: dict[str, Any]) -> CareerPublic:
        payload = dict(doc)
        payload["id"] = doc.doc_id  # type: ignore[attr-defined]
        return CareerPublic.model_validate(payload)
