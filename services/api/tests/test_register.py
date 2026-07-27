"""Tests for POST /users (register) and related auth entry."""

from __future__ import annotations


def test_register_happy_path(client):
    response = client.post(
        "/users",
        json={
            "email": "nuevo@example.com",
            "password": "segura123",
            "name": "Nuevo",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nuevo@example.com"
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert "hashed_password" not in body


def test_register_edge_min_password_length(client):
    """Password exactamente en el mínimo (8) debe aceptarse."""
    response = client.post(
        "/users",
        json={"email": "minpass@example.com", "password": "12345678"},
    )
    assert response.status_code == 201


def test_register_fail_duplicate_email(client, registered_user):
    response = client.post(
        "/users",
        json={
            "email": registered_user["email"],
            "password": "otraclave9",
        },
    )
    assert response.status_code == 409
    assert "email" in response.json()["detail"].lower()


def test_register_fail_empty_fields(client):
    response = client.post("/users", json={"email": "", "password": ""})
    assert response.status_code == 400
    payload = response.json()
    assert "errors" in payload or "detail" in payload


def test_register_fail_short_password(client):
    response = client.post(
        "/users",
        json={"email": "corto@example.com", "password": "1234567"},
    )
    assert response.status_code == 400
