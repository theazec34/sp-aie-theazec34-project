"""Tests for /api/incidents (public backoffice API group)."""

from __future__ import annotations


def test_incidents_create_and_summary_happy(client):
    create = client.post(
        "/api/incidents",
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

    summary = client.get("/api/incidents/summary")
    assert summary.status_code == 200
    data = summary.json()
    assert data["total"] >= 1
    assert data["by_status"].get("open", 0) >= 1


def test_incidents_list_edge_empty_filters(client):
    response = client.get("/api/incidents", params={"status": "resolved"})
    assert response.status_code == 200
    assert response.json() == []


def test_incidents_fail_invalid_transition(client):
    create = client.post(
        "/api/incidents",
        json={
            "title": "Queja cliente",
            "description": "Espera excesiva en sala",
            "category": "customer_complaint",
            "origin": "customer",
            "branch": "central",
        },
    )
    incident_id = create.json()["id"]

    # open → resolved no está permitido (debe pasar por in_progress)
    bad = client.patch(
        f"/api/incidents/{incident_id}/status",
        json={"status": "resolved"},
    )
    assert bad.status_code == 400


def test_incidents_fail_not_found(client):
    response = client.get("/api/incidents/99999")
    assert response.status_code == 404


def test_incidents_fail_empty_title(client):
    response = client.post(
        "/api/incidents",
        json={
            "title": "",
            "description": "desc",
            "category": "other",
            "origin": "internal",
            "branch": "central",
        },
    )
    assert response.status_code == 400
