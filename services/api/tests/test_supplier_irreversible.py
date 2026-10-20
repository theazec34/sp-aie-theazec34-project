"""BRIEFING §5 — suspender/eliminar proveedor exige admin + confirm=true."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.users.models import UserRole, UserUpdate
from app.users.repository import UserRepository


def _promote_admin(email: str) -> None:
    repo = UserRepository()
    try:
        user = repo.get_by_email(email)
        assert user is not None
        repo.update(user.id, UserUpdate(role=UserRole.ADMIN))
    finally:
        repo.close()


def test_supplier_status_requires_confirm_and_admin(
    client: TestClient,
    auth_header: dict[str, str],
    registered_user: dict[str, str],
):
    create = client.post(
        "/suppliers",
        headers=auth_header,
        json={
            "name": "Proveedor Critico",
            "country": "USA",
            "categories": ["packaging"],
            "rate_per_unit": 2.0,
            "currency": "USD",
            "status": "active",
        },
    )
    assert create.status_code == 201
    sid = create.json()["id"]

    # Usuario no-admin → 403 aunque confirme
    denied = client.patch(
        f"/suppliers/{sid}/status",
        headers=auth_header,
        json={"status": "suspended", "confirm": True},
    )
    assert denied.status_code == 403

    _promote_admin(registered_user["email"])
    # Re-login after role change (token still valid — role checked at request)
    # TinyDB update is live; same token's user_id reloads role from DB
    no_confirm = client.patch(
        f"/suppliers/{sid}/status",
        headers=auth_header,
        json={"status": "suspended", "confirm": False},
    )
    assert no_confirm.status_code == 400
    assert "confirm" in no_confirm.json()["detail"].lower()

    ok = client.patch(
        f"/suppliers/{sid}/status",
        headers=auth_header,
        json={"status": "suspended", "confirm": True},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "suspended"

    del_no = client.delete(f"/suppliers/{sid}", headers=auth_header)
    assert del_no.status_code == 400

    deleted = client.delete(
        f"/suppliers/{sid}?confirm=true", headers=auth_header
    )
    assert deleted.status_code == 204
