"""ChatSession (BRIEFING Parte 2) — rehidratación por session_id / thread_id."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

SessionStatus = Literal["active", "interrupted", "closed"]

AGENT_ID = "manager_support"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChatMessage:
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    status: Literal["complete", "streaming", "interrupted"] = "complete"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class ChatSession:
    session_id: str
    agent_id: str
    user_id: str
    location_id: str | None
    status: SessionStatus
    created_at: str
    messages: list[ChatMessage] = field(default_factory=list)
    # Generación activa (para abort genuino)
    active_generation_id: str | None = None
    active_message_id: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "location_id": self.location_id,
            "status": self.status,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages],
        }


class ChatSessionStore:
    """Almacén in-process (un worker). thread_id LangGraph = session_id."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, ChatSession] = {}

    def get_or_create(
        self,
        *,
        session_id: str | None,
        user_id: str,
        location_id: str | None = None,
    ) -> ChatSession:
        sid = (session_id or "").strip() or f"chat_{uuid.uuid4().hex[:8]}"
        with self._lock:
            existing = self._sessions.get(sid)
            if existing is not None:
                # Siempre actualizar sede al reconectar (el desplegable del UI)
                if location_id:
                    existing.location_id = location_id
                if existing.status == "closed":
                    existing.status = "active"
                return existing
            session = ChatSession(
                session_id=sid,
                agent_id=AGENT_ID,
                user_id=str(user_id),
                location_id=location_id,
                status="active",
                created_at=_now(),
            )
            self._sessions[sid] = session
            return session

    def get(self, session_id: str) -> ChatSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def append_message(self, session_id: str, message: ChatMessage) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            session.messages.append(message)

    def update_message(
        self,
        session_id: str,
        message_id: str,
        *,
        content: str | None = None,
        status: str | None = None,
    ) -> ChatMessage | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            for msg in session.messages:
                if msg.message_id == message_id:
                    if content is not None:
                        msg.content = content
                    if status is not None:
                        msg.status = status  # type: ignore[assignment]
                    return msg
            return None

    def set_status(self, session_id: str, status: SessionStatus) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                session.status = status

    def set_active_generation(
        self,
        session_id: str,
        *,
        generation_id: str | None,
        message_id: str | None,
    ) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            session.active_generation_id = generation_id
            session.active_message_id = message_id

    def reset_for_tests(self) -> None:
        with self._lock:
            self._sessions.clear()


_STORE = ChatSessionStore()


def get_session_store() -> ChatSessionStore:
    return _STORE
