"""TinyDB persistence for User credentials."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.users.models import UserInDB, UserPublic, UserRole, UserUpdate

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "auth.json"


class UserRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(self.db_path)
        self._table = self._db.table("users")

    def close(self) -> None:
        self._db.close()

    def count(self) -> int:
        return len(self._table)

    def list(self) -> list[UserPublic]:
        return [self._to_public(doc) for doc in self._table.all()]

    def get(self, user_id: int) -> UserInDB | None:
        doc = self._table.get(doc_id=user_id)
        if doc is None:
            return None
        return self._to_in_db(doc)

    def get_by_email(self, email: str) -> UserInDB | None:
        UserQ = Query()
        doc = self._table.get(UserQ.email == email.lower())
        if doc is None:
            return None
        return self._to_in_db(doc)

    def email_exists(self, email: str, exclude_id: int | None = None) -> bool:
        UserQ = Query()
        docs = self._table.search(UserQ.email == email.lower())
        if exclude_id is None:
            return bool(docs)
        return any(doc.doc_id != exclude_id for doc in docs)

    def create(
        self,
        *,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
    ) -> UserInDB:
        now = datetime.now(timezone.utc)
        data = {
            "email": email.lower(),
            "hashed_password": hashed_password,
            "is_active": is_active,
            "role": role.value,
            "created_at": now.isoformat(),
        }
        doc_id = self._table.insert(data)
        user = self.get(doc_id)
        assert user is not None
        return user

    def update(self, user_id: int, payload: UserUpdate) -> UserInDB | None:
        if self._table.get(doc_id=user_id) is None:
            return None
        patch: dict[str, Any] = {}
        if payload.email is not None:
            patch["email"] = str(payload.email).lower()
        if payload.role is not None:
            patch["role"] = payload.role.value
        if payload.is_active is not None:
            patch["is_active"] = payload.is_active
        if patch:
            self._table.update(patch, doc_ids=[user_id])
        return self.get(user_id)

    def update_password(self, user_id: int, hashed_password: str) -> UserInDB | None:
        if self._table.get(doc_id=user_id) is None:
            return None
        self._table.update({"hashed_password": hashed_password}, doc_ids=[user_id])
        return self.get(user_id)

    def delete(self, user_id: int) -> bool:
        if self._table.get(doc_id=user_id) is None:
            return False
        self._table.remove(doc_ids=[user_id])
        return True

    @staticmethod
    def _to_in_db(doc: dict[str, Any]) -> UserInDB:
        payload = dict(doc)
        payload["id"] = doc.doc_id  # type: ignore[attr-defined]
        if isinstance(payload.get("created_at"), str):
            payload["created_at"] = datetime.fromisoformat(payload["created_at"])
        return UserInDB.model_validate(payload)

    @staticmethod
    def _to_public(doc: dict[str, Any]) -> UserPublic:
        payload = dict(doc)
        payload["id"] = doc.doc_id  # type: ignore[attr-defined]
        if isinstance(payload.get("created_at"), str):
            payload["created_at"] = datetime.fromisoformat(payload["created_at"])
        payload.pop("hashed_password", None)
        return UserPublic.model_validate(payload)
