"""TinyDB persistence for the Brasaland supplier directory."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from app.suppliers.models import (
    ProductCategory,
    Supplier,
    SupplierCreate,
    SupplierStatus,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "suppliers.json"


class SupplierRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(self.db_path)
        self._table = self._db.table("suppliers")

    def close(self) -> None:
        self._db.close()

    def count(self) -> int:
        return len(self._table)

    def list(
        self,
        country: str | None = None,
        category: str | None = None,
    ) -> list[Supplier]:
        docs = self._table.all()
        if country:
            docs = [d for d in docs if d.get("country") == country]
        if category:
            docs = [d for d in docs if category in (d.get("categories") or [])]
        return [self._to_supplier(doc) for doc in docs]

    def get(self, supplier_id: int) -> Supplier | None:
        doc = self._table.get(doc_id=supplier_id)
        if doc is None:
            return None
        return self._to_supplier(doc)

    def create(self, payload: SupplierCreate) -> Supplier:
        now = datetime.now(timezone.utc)
        data = payload.model_dump(mode="json")
        data["updated_at"] = now.isoformat()
        doc_id = self._table.insert(data)
        return self.get(doc_id)  # type: ignore[return-value]

    def update_rate(self, supplier_id: int, rate_per_unit: float) -> Supplier | None:
        if self._table.get(doc_id=supplier_id) is None:
            return None
        now = datetime.now(timezone.utc)
        self._table.update(
            {"rate_per_unit": rate_per_unit, "updated_at": now.isoformat()},
            doc_ids=[supplier_id],
        )
        return self.get(supplier_id)

    def update_status(
        self, supplier_id: int, status: SupplierStatus
    ) -> Supplier | None:
        if self._table.get(doc_id=supplier_id) is None:
            return None
        self._table.update({"status": status.value}, doc_ids=[supplier_id])
        return self.get(supplier_id)

    def delete(self, supplier_id: int) -> bool:
        if self._table.get(doc_id=supplier_id) is None:
            return False
        self._table.remove(doc_ids=[supplier_id])
        return True

    def name_exists(self, name: str) -> bool:
        SupplierQ = Query()
        return self._table.contains(SupplierQ.name == name)

    def seed_if_empty(self, rows: list[dict[str, Any]]) -> tuple[int, int]:
        """Insert seed rows that are not already present (by name). Returns (inserted, skipped)."""
        inserted = 0
        skipped = 0
        for row in rows:
            if self.name_exists(row["name"]):
                skipped += 1
                continue
            create = SupplierCreate.model_validate(row)
            self.create(create)
            inserted += 1
        return inserted, skipped

    @staticmethod
    def _to_supplier(doc: dict[str, Any]) -> Supplier:
        payload = dict(doc)
        payload["id"] = doc.doc_id  # type: ignore[attr-defined]
        if isinstance(payload.get("updated_at"), str):
            payload["updated_at"] = datetime.fromisoformat(payload["updated_at"])
        # Normalize categories to enum-friendly values
        payload["categories"] = [
            ProductCategory(c) if not isinstance(c, ProductCategory) else c
            for c in payload.get("categories", [])
        ]
        return Supplier.model_validate(payload)
