"""Public reservations & careers intake."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.public_intake.router as intake_router
from app.public_intake.repository import PublicIntakeRepository


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "public_intake.json"
    store = PublicIntakeRepository(db_path=db_path)
    monkeypatch.setattr(intake_router, "_repo", store)
    intake_router._public_limiter.reset_for_tests()
    with TestClient(app) as c:
        yield c


def test_create_reservation(client: TestClient) -> None:
    res = client.post(
        "/reservations",
        json={
            "full_name": "Ana Pérez",
            "phone": "+34 600 111 222",
            "email": "ana@example.com",
            "date": "2030-06-15",
            "time": "21:00",
            "guests": 4,
            "notes": "Terraza si es posible",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["id"] >= 1
    assert body["status"] == "received"
    assert "no está confirmada" in body["message"].lower()


def test_list_reservations_requires_auth(client: TestClient) -> None:
    assert client.get("/reservations").status_code == 401


def test_create_career(client: TestClient) -> None:
    res = client.post(
        "/careers",
        json={
            "name": "Luis Gómez",
            "email": "luis@example.com",
            "phone": "+34600111222",
            "department": "Sala",
            "experience_years": 3,
            "message": "Experiencia en sala de brasería y barra.",
            "cv_filename": "cv-luis.pdf",
            "privacy_accepted": True,
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["department"] == "Sala"
    assert "status_message" in body


def test_career_requires_privacy(client: TestClient) -> None:
    res = client.post(
        "/careers",
        json={
            "name": "Luis Gómez",
            "email": "luis@example.com",
            "phone": "+34600111222",
            "department": "Sala",
            "experience_years": 3,
            "message": "Experiencia en sala de brasería y barra.",
            "privacy_accepted": False,
        },
    )
    assert res.status_code in (400, 422)
