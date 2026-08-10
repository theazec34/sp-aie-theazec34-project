"""Pytest fixtures: isolated TinyDB + FastAPI TestClient."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure settings load with a test secret before app import
os.environ["SECRET_KEY"] = "pytest-brasaland-secret-key"
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("RESET_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
# Avoid real Resend calls in tests (console fallback)
os.environ["RESEND_API_KEY"] = ""


@pytest.fixture()
def tmp_dbs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    auth_db = tmp_path / "auth.json"
    suppliers_db = tmp_path / "suppliers.json"
    incidents_db = tmp_path / "incidents.json"

    # Clear settings cache so env overrides apply
    from app.auth import config as auth_config

    auth_config.get_settings.cache_clear()

    monkeypatch.setattr("app.users.repository.DEFAULT_DB_PATH", auth_db)
    monkeypatch.setattr("app.profiles.repository.DEFAULT_DB_PATH", auth_db)
    monkeypatch.setattr("app.auth.reset_tokens.DEFAULT_DB_PATH", auth_db)
    monkeypatch.setattr("app.auth.email.DEFAULT_DB_PATH", auth_db)
    monkeypatch.setattr("app.suppliers.repository.DEFAULT_DB_PATH", suppliers_db)
    monkeypatch.setattr("app.incidents.repository.DEFAULT_DB_PATH", incidents_db)

    return {
        "auth": auth_db,
        "suppliers": suppliers_db,
        "incidents": incidents_db,
    }


@pytest.fixture()
def client(tmp_dbs: dict[str, Path]) -> TestClient:
    from app.cache import incidents_cache, suppliers_cache
    from app.main import app

    incidents_cache.clear()
    suppliers_cache.clear()
    return TestClient(app)


@pytest.fixture()
def registered_user(client: TestClient) -> dict[str, str]:
    email = "tester@example.com"
    password = "Password1!"
    response = client.post(
        "/users",
        json={
            "email": email,
            "password": password,
            "name": "Tester",
            "phone": None,
            "address": None,
        },
    )
    assert response.status_code == 201, response.text
    return {"email": email, "password": password}


@pytest.fixture()
def auth_header(client: TestClient, registered_user: dict[str, str]) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
