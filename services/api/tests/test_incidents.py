"""Tests for /api/incidents — JWT required (OWASP A01 fix)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_incidents_require_jwt(client: TestClient):
    assert client.get("/api/incidents").status_code in {401, 403}
    assert client.post(
        "/api/incidents",
        json={
            "title": "Sin auth",
            "description": "no",
            "category": "other",
            "origin": "internal",
            "branch": "central",
        },
    ).status_code in {401, 403}


def test_incidents_create_and_summary_happy(
    client: TestClient, auth_header: dict[str, str]
):
    create = client.post(
        "/api/incidents",
        headers=auth_header,
        json={
            "title": "Fallo TPV",
            "description": "La caja no imprime tickets",
            "category": "pos_system",
            "origin": "branch",
            "branch": "miami_doral",
        },
    )
    assert create.status_code == 201
    body = create.json()
    assert body["status"] == "open"
    assert body["branch"] == "miami_doral"

    summary = client.get("/api/incidents/summary", headers=auth_header)
    assert summary.status_code == 200
    data = summary.json()
    assert data["total"] >= 1
    assert data["by_status"].get("open", 0) >= 1


def test_incidents_list_edge_empty_filters(
    client: TestClient, auth_header: dict[str, str]
):
    response = client.get(
        "/api/incidents", headers=auth_header, params={"status": "resolved"}
    )
    assert response.status_code == 200
    assert response.json() == []


def test_incidents_fail_invalid_transition(
    client: TestClient, auth_header: dict[str, str]
):
    create = client.post(
        "/api/incidents",
        headers=auth_header,
        json={
            "title": "Queja cliente",
            "description": "Espera excesiva en sala",
            "category": "customer_complaint",
            "origin": "customer",
            "branch": "central",
        },
    )
    incident_id = create.json()["id"]

    bad = client.patch(
        f"/api/incidents/{incident_id}/status",
        headers=auth_header,
        json={"status": "resolved"},
    )
    assert bad.status_code == 400


def test_incidents_fail_not_found(client: TestClient, auth_header: dict[str, str]):
    response = client.get("/api/incidents/99999", headers=auth_header)
    assert response.status_code == 404


def test_incidents_fail_empty_title(client: TestClient, auth_header: dict[str, str]):
    response = client.post(
        "/api/incidents",
        headers=auth_header,
        json={
            "title": "",
            "description": "desc",
            "category": "other",
            "origin": "internal",
            "branch": "central",
        },
    )
    assert response.status_code == 400
