"""Single-use password-reset token registry (TinyDB)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.users.repository import DEFAULT_DB_PATH


class PasswordResetTokenRepository:
    """Stores JWT `jti` values so reset tokens are strictly single-use."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(self.db_path)
        self._table = self._db.table("password_reset_tokens")

    def close(self) -> None:
        self._db.close()

    def create(self, *, jti: str, user_id: int, expires_at: datetime) -> None:
        self._table.insert(
            {
                "jti": jti,
                "user_id": user_id,
                "expires_at": expires_at.astimezone(timezone.utc).isoformat(),
                "used_at": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_by_jti(self, jti: str) -> dict[str, Any] | None:
        TokenQ = Query()
        doc = self._table.get(TokenQ.jti == jti)
        if doc is None:
            return None
        payload = dict(doc)
        payload["doc_id"] = doc.doc_id  # type: ignore[attr-defined]
        return payload

    def is_usable(self, jti: str) -> bool:
        row = self.get_by_jti(jti)
        if row is None:
            return False
        if row.get("used_at"):
            return False
        expires_raw = row.get("expires_at")
        if not isinstance(expires_raw, str):
            return False
        expires_at = datetime.fromisoformat(expires_raw)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)

    def mark_used(self, jti: str) -> bool:
        row = self.get_by_jti(jti)
        if row is None:
            return False
        if row.get("used_at"):
            return False
        self._table.update(
            {"used_at": datetime.now(timezone.utc).isoformat()},
            doc_ids=[row["doc_id"]],
        )
        return True
