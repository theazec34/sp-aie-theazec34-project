"""seed_public_intake creates demo rows idempotently."""

from __future__ import annotations

from pathlib import Path

from app.public_intake.repository import PublicIntakeRepository
from seed_public_intake import main as seed_main


def test_seed_public_intake_idempotent(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "public_intake.json"
    db.write_text("", encoding="utf-8")  # empty file repair path
    monkeypatch.setattr(
        "seed_public_intake.PublicIntakeRepository",
        lambda: PublicIntakeRepository(db_path=db),
    )
    assert seed_main() == 0
    assert seed_main() == 0
    repo = PublicIntakeRepository(db_path=db)
    try:
        assert len(repo.list_reservations()) == 1
        assert len(repo.list_careers()) == 1
    finally:
        repo.close()
