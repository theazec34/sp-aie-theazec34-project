"""TinyDB persistence for Profile (1:1 with User)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.profiles.models import Profile, ProfileUpdate
from app.users.repository import DEFAULT_DB_PATH


class ProfileRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(self.db_path)
        self._table = self._db.table("profiles")

    def close(self) -> None:
        self._db.close()

    def get(self, profile_id: int) -> Profile | None:
        doc = self._table.get(doc_id=profile_id)
        if doc is None:
            return None
        return self._to_profile(doc)

    def get_by_user_id(self, user_id: int) -> Profile | None:
        ProfileQ = Query()
        doc = self._table.get(ProfileQ.user_id == user_id)
        if doc is None:
            return None
        return self._to_profile(doc)

    def create(
        self,
        *,
        user_id: int,
        name: str = "",
        phone: str | None = None,
        address: str | None = None,
    ) -> Profile:
        data = {
            "user_id": user_id,
            "name": name or "",
            "phone": phone,
            "address": address,
        }
        doc_id = self._table.insert(data)
        profile = self.get(doc_id)
        assert profile is not None
        return profile

    def update_for_user(self, user_id: int, payload: ProfileUpdate) -> Profile | None:
        existing = self.get_by_user_id(user_id)
        if existing is None:
            return self.create(
                user_id=user_id,
                name=payload.name,
                phone=payload.phone,
                address=payload.address,
            )
        self._table.update(
            {
                "name": payload.name,
                "phone": payload.phone,
                "address": payload.address,
            },
            doc_ids=[existing.id],
        )
        return self.get(existing.id)

    def delete_by_user_id(self, user_id: int) -> bool:
        ProfileQ = Query()
        removed = self._table.remove(ProfileQ.user_id == user_id)
        return bool(removed)

    @staticmethod
    def _to_profile(doc: dict[str, Any]) -> Profile:
        payload = dict(doc)
        payload["id"] = doc.doc_id  # type: ignore[attr-defined]
        return Profile.model_validate(payload)
