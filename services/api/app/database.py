"""SQLModel engine for inventory (Postgres/Supabase or local SQLite).

Auth, users, profiles, suppliers and incidents keep using TinyDB in their
own repositories — there is no User table in this SQL database.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_DEFAULT_SQLITE = f"sqlite:///{(_DATA_DIR / 'inventory.db').as_posix()}"
_FALLBACK_MARKER = _DATA_DIR / ".sqlite_fallback"


def _sqlite_url() -> str:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_SQLITE


def _try_engine(url: str):
    connect_args: dict = {}
    kwargs: dict = {"echo": False}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    elif url.startswith("postgres"):
        # Short timeout so Docker boot stays snappy if Supabase is blocked.
        connect_args = {"connect_timeout": 3}
        kwargs["pool_pre_ping"] = True
    kwargs["connect_args"] = connect_args
    eng = create_engine(url, **kwargs)
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    return eng


def _build_engine():
    """Prefer DATABASE_URL (Supabase); fall back to SQLite if unreachable.

    Remembers a failed Postgres probe via `.sqlite_fallback` so uvicorn --reload
    does not re-wait on DNS/timeouts for every worker spawn. Delete that file
    (or the data volume) to retry Supabase.
    """
    configured = (os.getenv("DATABASE_URL") or "").strip()
    if configured and not _FALLBACK_MARKER.exists():
        try:
            return _try_engine(configured), configured
        except Exception as exc:  # noqa: BLE001
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            _FALLBACK_MARKER.write_text("postgres unreachable\n", encoding="utf-8")
            print(
                f"[database] WARN — DATABASE_URL unreachable ({exc}); "
                "falling back to local SQLite "
                f"(marker {_FALLBACK_MARKER.name}).",
                flush=True,
            )
    elif configured and _FALLBACK_MARKER.exists():
        print(
            "[database] Using SQLite fallback "
            f"(remove {_FALLBACK_MARKER} to retry DATABASE_URL).",
            flush=True,
        )

    url = _sqlite_url()
    return _try_engine(url), url


engine, DATABASE_URL = _build_engine()


def init_db() -> None:
    """Create tables registered on SQLModel.metadata (call after importing models)."""
    SQLModel.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one SQLModel session per request."""
    with Session(engine) as session:
        yield session
