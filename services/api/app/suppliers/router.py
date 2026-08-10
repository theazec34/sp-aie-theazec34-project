"""FastAPI routes for Brasaland supplier directory (JWT protected)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.auth.deps import get_current_user
from app.cache import SUPPLIERS_LIST_TTL, suppliers_cache
from app.suppliers.models import (
    ProductCategory,
    Country,
    Supplier,
    SupplierCreate,
    SupplierRateUpdate,
    SupplierStatusUpdate,
)
from app.suppliers.repository import SupplierRepository
from app.users.models import UserInDB

router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
    dependencies=[Depends(get_current_user)],
)


def get_repo() -> SupplierRepository:
    return SupplierRepository()


def _list_cache_key(country: str | None, category: str | None) -> str:
    # Shared across authenticated users — directory is not user-scoped.
    return f"suppliers:list:country={country or '*'}:category={category or '*'}"


def _invalidate_supplier_lists() -> None:
    suppliers_cache.invalidate_prefix("suppliers:list:")


@router.post("", response_model=Supplier, status_code=201)
def create_supplier(
    payload: SupplierCreate, _current: UserInDB = Depends(get_current_user)
) -> Supplier:
    repo = get_repo()
    try:
        if repo.name_exists(payload.name):
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un proveedor con el nombre '{payload.name}'.",
            )
        created = repo.create(payload)
        _invalidate_supplier_lists()
        return created
    finally:
        repo.close()


@router.get("", response_model=list[Supplier])
def list_suppliers(
    response: Response,
    country: Country | None = Query(default=None),
    category: ProductCategory | None = Query(default=None),
    _current: UserInDB = Depends(get_current_user),
) -> list[Supplier]:
    country_v = country.value if country else None
    category_v = category.value if category else None
    key = _list_cache_key(country_v, category_v)

    cached = suppliers_cache.get(key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return [Supplier.model_validate(item) for item in cached]

    repo = get_repo()
    try:
        items = repo.list(country=country_v, category=category_v)
        suppliers_cache.set(
            key,
            [item.model_dump(mode="json") for item in items],
            SUPPLIERS_LIST_TTL,
        )
        response.headers["X-Cache"] = "MISS"
        return items
    finally:
        repo.close()


@router.get("/{supplier_id}", response_model=Supplier)
def get_supplier(
    supplier_id: int, _current: UserInDB = Depends(get_current_user)
) -> Supplier:
    repo = get_repo()
    try:
        supplier = repo.get(supplier_id)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
        return supplier
    finally:
        repo.close()


@router.patch("/{supplier_id}/rate", response_model=Supplier)
def update_supplier_rate(
    supplier_id: int,
    payload: SupplierRateUpdate,
    _current: UserInDB = Depends(get_current_user),
) -> Supplier:
    repo = get_repo()
    try:
        supplier = repo.update_rate(supplier_id, payload.rate_per_unit)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
        _invalidate_supplier_lists()
        return supplier
    finally:
        repo.close()


@router.patch("/{supplier_id}/status", response_model=Supplier)
def update_supplier_status(
    supplier_id: int,
    payload: SupplierStatusUpdate,
    _current: UserInDB = Depends(get_current_user),
) -> Supplier:
    repo = get_repo()
    try:
        supplier = repo.update_status(supplier_id, payload.status)
        if supplier is None:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
        _invalidate_supplier_lists()
        return supplier
    finally:
        repo.close()


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: int, _current: UserInDB = Depends(get_current_user)
) -> None:
    repo = get_repo()
    try:
        deleted = repo.delete(supplier_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado.")
        _invalidate_supplier_lists()
    finally:
        repo.close()
