"""Tests for POST /auth/login and GET /auth/me (+ token failure modes)."""

from __future__ import annotations

from jose import jwt

from app.auth.security import hash_password
from app.users.models import UserRole, UserUpdate
from app.users.repository import UserRepository


def test_login_happy_path(client, registered_user):
    response = client.post(
        "/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("token_type") == "bearer"
    assert isinstance(body.get("access_token"), str)
    assert len(body["access_token"]) > 20


def test_login_fail_wrong_password(client, registered_user):
    response = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": "wrong-pass"},
    )
    assert response.status_code == 401


def test_login_fail_unknown_email(client):
    response = client.post(
        "/auth/login",
        data={"username": "noexiste@example.com", "password": "Password1!"},
    )
    assert response.status_code == 401


def test_login_edge_inactive_user(client, registered_user):
    repo = UserRepository()
    try:
        user = repo.get_by_email(registered_user["email"])
        assert user is not None
        repo.update(user.id, UserUpdate(is_active=False))
    finally:
        repo.close()

    response = client.post(
        "/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 401


def test_login_fail_empty_form(client):
    response = client.post("/auth/login", data={"username": "", "password": ""})
    # FastAPI/OAuth2 may 400 (our handler) or 422 mapped to 400
    assert response.status_code in {400, 401, 422}


def test_me_happy_path(client, auth_header, registered_user):
    response = client.get("/auth/me", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == registered_user["email"]
    assert body["role"] == "user"
    assert body.get("profile") is not None
    assert body["profile"]["name"] == "Tester"


def test_me_fail_missing_token(client):
    response = client.get("/auth/me")
    assert response.status_code in {401, 403}


def test_me_fail_malformed_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


def test_me_fail_token_wrong_secret(client, registered_user):
    """JWT firmado con otra clave no debe autenticar."""
    # Need a real user id in subject — forge with wrong secret
    repo = UserRepository()
    try:
        user = repo.get_by_email(registered_user["email"])
        assert user is not None
        user_id = user.id
    finally:
        repo.close()

    forged = jwt.encode(
        {"sub": str(user_id)},
        "another-secret-not-used-by-app",
        algorithm="HS256",
    )
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert response.status_code == 401
