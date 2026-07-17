"""FastAPI routes for Brasaland supplier directory."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.suppliers.models import (
    ProductCategory,
    Country,
    Supplier,
    SupplierCreate,
    SupplierRateUpdate,
    SupplierStatusUpdate,
)
from app.suppliers.repository import SupplierRepository

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def get_repo() -> SupplierRepository:
    return SupplierRepository()


@router.post("", response_model=Supplier, status_code=201)
def create_supplier(payload: SupplierCreate) -> Supplier:
    repo = get_repo()
    try:
        if repo.name_exists(payload.name):
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un proveedor con el nombre '{payload.name}'.",
            )
        return repo.create(payload)
    finally:
        repo.close()


@router.get("", response_model=list[Supplier])
def list_suppliers(
    country: Country | None = Query(default=None),
    category: ProductCategory | None = Query(default=None),
) -> list[Supplier]:
    repo = get_repo()
    try:
        return repo.list(
            country=country.value if country else None,
            category=category.value if category else None,
        )
    finally:
        repo.close()


@router.get("/{supplier_id}", response_model=Supplier)
def get_supplier(supplier_id: int) -> Supplier:
    repo = get_repo()
    try:
        supplier = repo.get(supplier_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
        return supplier
    finally:
        repo.close()


@router.patch("/{supplier_id}/rate", response_model=Supplier)
def update_supplier_rate(supplier_id: int, payload: SupplierRateUpdate) -> Supplier:
    repo = get_repo()
    try:
        supplier = repo.update_rate(supplier_id, payload.rate_per_unit)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
        return supplier
    finally:
        repo.close()


@router.patch("/{supplier_id}/status", response_model=Supplier)
def update_supplier_status(
    supplier_id: int, payload: SupplierStatusUpdate
) -> Supplier:
    repo = get_repo()
    try:
        supplier = repo.update_status(supplier_id, payload.status)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
        return supplier
    finally:
        repo.close()


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(supplier_id: int) -> None:
    repo = get_repo()
    try:
        deleted = repo.delete(supplier_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
    finally:
        repo.close()
