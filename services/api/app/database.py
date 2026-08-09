"""SQLModel engine for inventory (Postgres/Supabase or local SQLite).

Auth, users, profiles, suppliers and incidents keep using TinyDB in their
own repositories — there is no User table in this SQL database.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_DEFAULT_SQLITE = f"sqlite:///{(_DATA_DIR / 'inventory.db').as_posix()}"


def _database_url() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if url:
        return url
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_SQLITE


DATABASE_URL = _database_url()

_connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, echo=False, connect_args=_connect_args)


def init_db() -> None:
    """Create tables registered on SQLModel.metadata (call after importing models)."""
    SQLModel.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one SQLModel session per request."""
    with Session(engine) as session:
        yield session
