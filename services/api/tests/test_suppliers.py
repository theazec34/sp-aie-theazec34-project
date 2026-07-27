"""Tests for /suppliers (non-auth backoffice API group)."""

from __future__ import annotations


def _auth(client) -> dict[str, str]:
    client.post(
        "/users",
        json={"email": "buyer@example.com", "password": "Password1!", "name": "Buyer"},
    )
    login = client.post(
        "/auth/login",
        data={"username": "buyer@example.com", "password": "Password1!"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_suppliers_list_happy_empty(client):
    headers = _auth(client)
    response = client.get("/suppliers", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_suppliers_create_happy(client):
    headers = _auth(client)
    response = client.post(
        "/suppliers",
        headers=headers,
        json={
            "name": "Carbones Andinos",
            "country": "Colombia",
            "categories": ["carbon_y_combustible"],
            "rate_per_unit": 12.5,
            "currency": "COP",
            "status": "active",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Carbones Andinos"
    assert body["currency"] == "COP"

    listed = client.get("/suppliers", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_suppliers_edge_filter_unknown_country_returns_empty(client):
    headers = _auth(client)
    client.post(
        "/suppliers",
        headers=headers,
        json={
            "name": "Solo USA",
            "country": "USA",
            "categories": ["packaging"],
            "rate_per_unit": 3.0,
            "currency": "USD",
            "status": "active",
        },
    )
    response = client.get("/suppliers", headers=headers, params={"country": "Colombia"})
    assert response.status_code == 200
    assert response.json() == []


def test_suppliers_fail_invalid_currency_for_country(client):
    headers = _auth(client)
    response = client.post(
        "/suppliers",
        headers=headers,
        json={
            "name": "Malo",
            "country": "Colombia",
            "categories": ["carne"],
            "rate_per_unit": 1.0,
            "currency": "USD",  # debe ser COP
            "status": "active",
        },
    )
    assert response.status_code == 400


def test_suppliers_fail_unauthorized(client):
    response = client.get("/suppliers")
    assert response.status_code in {401, 403}
