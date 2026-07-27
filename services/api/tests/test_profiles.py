"""Tests for GET/PUT /profiles/me."""

from __future__ import annotations


def test_get_profile_happy(client, auth_header):
    response = client.get("/profiles/me", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Tester"


def test_update_profile_happy(client, auth_header):
    response = client.put(
        "/profiles/me",
        headers=auth_header,
        json={"name": "Tester Updated", "phone": "600111222", "address": "Calle 1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Tester Updated"
    assert body["phone"] == "600111222"


def test_update_profile_edge_nullable_fields(client, auth_header):
    response = client.put(
        "/profiles/me",
        headers=auth_header,
        json={"name": "Solo Nombre", "phone": None, "address": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Solo Nombre"
    assert body.get("phone") in (None, "")


def test_profile_fail_unauthorized(client):
    response = client.put(
        "/profiles/me",
        json={"name": "Hack"},
    )
    assert response.status_code in {401, 403}
