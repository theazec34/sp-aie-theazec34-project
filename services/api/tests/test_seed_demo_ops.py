"""seed_demo_ops creates multi-branch demo rows."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import Session, select


@pytest.fixture()
def demo_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SEED_DEMO_FORCE", "0")
    db_url = f"sqlite:///{tmp_path / 'inv.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    from sqlalchemy import create_engine
    from sqlmodel import SQLModel

    import app.database as dbmod
    import app.inventory.models  # noqa: F401
    import app.incidents.repository as inc_repo
    import app.public_intake.repository as intake_repo
    import app.suppliers.repository as sup_repo
    import app.users.repository as user_repo

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "DATABASE_URL", db_url)
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr(sup_repo, "DEFAULT_DB_PATH", tmp_path / "suppliers.json")
    monkeypatch.setattr(intake_repo, "DEFAULT_DB_PATH", tmp_path / "public_intake.json")
    monkeypatch.setattr(inc_repo, "DEFAULT_DB_PATH", tmp_path / "incidents.json")
    monkeypatch.setattr(user_repo, "DEFAULT_DB_PATH", tmp_path / "users.json")

    from app.auth.security import hash_password
    from app.users.repository import UserRepository

    users = UserRepository()
    try:
        users.create(
            email="admin@brasaland.com",
            hashed_password=hash_password("ChangeMeLocalOnly12!"),
        )
    finally:
        users.close()

    yield tmp_path, engine


def test_seed_demo_ops_multi_branch(demo_env):
    _tmp, engine = demo_env
    import seed_demo_ops as demo

    stats_sup = demo.seed_suppliers_by_branch()
    assert stats_sup["suppliers_total"] >= 15

    stats_res = demo.seed_reservations_and_careers()
    assert stats_res["reservations_total"] >= 18  # 9 sedes × hoy/mañana
    assert stats_res["careers_total"] >= 9

    # Base inventory SKUs then movements
    import seed_inventory

    assert seed_inventory.main() == 0
    stats_inv = demo.seed_inventory_movements()
    assert stats_inv["entries_total"] >= 4

    stats_inc = demo.seed_incidents_by_branch()
    assert stats_inc["incidents_total"] >= 9

    from app.inventory.models import IngredientEntry
    from app.public_intake.repository import PublicIntakeRepository
    from app.suppliers.repository import SupplierRepository

    with Session(engine) as session:
        entries = list(session.exec(select(IngredientEntry)).all())
        assert any("Demo" in (e.supplier_name or "") for e in entries)

    sup = SupplierRepository()
    try:
        assert any("branch=miami_doral" in (s.notes or "") for s in sup.list())
        top = max(sup.list(), key=lambda s: s.rate_per_unit)
        assert top.rate_per_unit >= 22
    finally:
        sup.close()

    intake = PublicIntakeRepository()
    try:
        notes = " ".join(r.notes for r in intake.list_reservations())
        assert "sede:miami_doral" in notes
        assert "sede:medellin_centro" in notes
    finally:
        intake.close()
