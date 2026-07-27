"""Tests for forgot-password, reset-password and change-password."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.auth.reset_tokens import PasswordResetTokenRepository
from app.auth.security import create_password_reset_token
from app.users.repository import UserRepository


def test_forgot_password_happy_registered(client, registered_user):
    response = client.post(
        "/auth/forgot-password",
        json={"email": registered_user["email"]},
    )
    assert response.status_code == 200
    assert "enlace" in response.json()["message"].lower() or "sistema" in response.json()[
        "message"
    ].lower()


def test_forgot_password_edge_unknown_email_still_200(client):
    """Anti-enumeración: mismo 200 aunque el email no exista."""
    response = client.post(
        "/auth/forgot-password",
        json={"email": "fantasma@example.com"},
    )
    assert response.status_code == 200
    msg = response.json()["message"]
    assert isinstance(msg, str) and len(msg) > 10


def test_forgot_password_fail_invalid_email(client):
    response = client.post(
        "/auth/forgot-password",
        json={"email": "no-es-un-email"},
    )
    assert response.status_code == 400


def test_reset_password_happy_path(client, registered_user):
    repo = UserRepository()
    tokens = PasswordResetTokenRepository()
    try:
        user = repo.get_by_email(registered_user["email"])
        assert user is not None
        token, jti, expires_at = create_password_reset_token(user_id=user.id)
        tokens.create(jti=jti, user_id=user.id, expires_at=expires_at)
    finally:
        repo.close()
        tokens.close()

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "NuevaPass9"},
    )
    assert response.status_code == 200

    login = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": "NuevaPass9"},
    )
    assert login.status_code == 200


def test_reset_password_edge_min_length(client, registered_user):
    repo = UserRepository()
    tokens = PasswordResetTokenRepository()
    try:
        user = repo.get_by_email(registered_user["email"])
        assert user is not None
        token, jti, expires_at = create_password_reset_token(user_id=user.id)
        tokens.create(jti=jti, user_id=user.id, expires_at=expires_at)
    finally:
        repo.close()
        tokens.close()

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "12345678"},
    )
    assert response.status_code == 200


def test_reset_password_fail_malformed_token(client):
    response = client.post(
        "/auth/reset-password",
        json={"token": "token-basura", "new_password": "NuevaPass9"},
    )
    assert response.status_code == 400


def test_reset_password_fail_reused_token(client, registered_user):
    repo = UserRepository()
    tokens = PasswordResetTokenRepository()
    try:
        user = repo.get_by_email(registered_user["email"])
        assert user is not None
        token, jti, expires_at = create_password_reset_token(user_id=user.id)
        tokens.create(jti=jti, user_id=user.id, expires_at=expires_at)
    finally:
        repo.close()
        tokens.close()

    first = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "Primera9x"},
    )
    assert first.status_code == 200

    second = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "Segunda9x"},
    )
    assert second.status_code == 400


def test_reset_password_fail_expired_jti(client, registered_user):
    """jti registrado ya caducado → 400 aunque el JWT se acepte o no."""
    repo = UserRepository()
    tokens = PasswordResetTokenRepository()
    try:
        user = repo.get_by_email(registered_user["email"])
        assert user is not None
        token, jti, _expires = create_password_reset_token(user_id=user.id)
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        tokens.create(jti=jti, user_id=user.id, expires_at=past)
    finally:
        repo.close()
        tokens.close()

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "NuevaPass9"},
    )
    assert response.status_code == 400


def test_change_password_happy(client, auth_header, registered_user):
    response = client.post(
        "/auth/change-password",
        headers=auth_header,
        json={
            "current_password": registered_user["password"],
            "new_password": "Cambiada12",
        },
    )
    assert response.status_code == 200

    old_login = client.post(
        "/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/auth/login",
        data={"username": registered_user["email"], "password": "Cambiada12"},
    )
    assert new_login.status_code == 200


def test_change_password_edge_same_as_current(client, auth_header, registered_user):
    response = client.post(
        "/auth/change-password",
        headers=auth_header,
        json={
            "current_password": registered_user["password"],
            "new_password": registered_user["password"],
        },
    )
    assert response.status_code == 400


def test_change_password_fail_wrong_current(client, auth_header):
    response = client.post(
        "/auth/change-password",
        headers=auth_header,
        json={"current_password": "incorrecta", "new_password": "Cambiada12"},
    )
    assert response.status_code == 400


def test_change_password_fail_unauthorized(client):
    response = client.post(
        "/auth/change-password",
        json={"current_password": "Password1!", "new_password": "Cambiada12"},
    )
    assert response.status_code in {401, 403}
