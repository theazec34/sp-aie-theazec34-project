"""Pydantic models for Brasaland supplier directory (CONTEXT exact fields)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Country(str, Enum):
    SPAIN = "España"
    COLOMBIA = "Colombia"
    USA = "USA"


class Currency(str, Enum):
    """Demo Brasaland Sevilla: todas las tarifas se expresan en euros."""

    EUR = "EUR"


class SupplierStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class ProductCategory(str, Enum):
    CARNE = "carne"
    VERDURAS = "verduras_y_hortalizas"
    SALSAS = "salsas_y_condimentos"
    BEBIDAS = "bebidas"
    PACKAGING = "packaging"
    LIMPIEZA = "productos_limpieza"
    LACTEOS = "lacteos"
    CARBON = "carbon_y_combustible"


VALID_CATEGORIES = {c.value for c in ProductCategory}

# Tasas approx. para convertir seeds históricos → EUR (demo)
FX_TO_EUR = {
    "EUR": 1.0,
    "USD": 0.92,
    "COP": 1.0 / 4300.0,
}

PositiveRate = Annotated[float, Field(gt=0, description="Tarifa vigente por unidad (> 0)")]


class SupplierBase(BaseModel):
    name: str = Field(min_length=1)
    country: Country
    categories: list[ProductCategory] = Field(min_length=1)
    rate_per_unit: PositiveRate
    currency: Currency = Currency.EUR
    status: SupplierStatus
    contact_email: str | None = None
    notes: str | None = None

    @field_validator("categories")
    @classmethod
    def categories_not_empty(cls, value: list[ProductCategory]) -> list[ProductCategory]:
        if not value:
            raise ValueError("categories must contain at least one valid category")
        return value

    @field_validator("contact_email")
    @classmethod
    def email_format(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("contact_email must be a valid email address")
        return value

    @model_validator(mode="before")
    @classmethod
    def coerce_currency_to_eur(cls, data: Any) -> Any:  # noqa: ANN401
        if not isinstance(data, dict):
            return data
        raw_cur = str(data.get("currency") or "EUR").upper()
        rate = data.get("rate_per_unit")
        if raw_cur != "EUR" and rate is not None:
            fx = FX_TO_EUR.get(raw_cur, 1.0)
            try:
                data = {
                    **data,
                    "rate_per_unit": round(float(rate) * fx, 4),
                    "currency": "EUR",
                }
            except (TypeError, ValueError):
                data = {**data, "currency": "EUR"}
        else:
            data = {**data, "currency": "EUR"}
        return data


class SupplierCreate(SupplierBase):
    """Input model for POST /suppliers — no id or updated_at from client."""


class SupplierRateUpdate(BaseModel):
    rate_per_unit: PositiveRate


class SupplierStatusUpdate(BaseModel):
    status: SupplierStatus
    # BRIEFING §5 — acción irreversible: requiere confirmación humana explícita
    confirm: bool = False


class Supplier(SupplierBase):
    """Response model including TinyDB document id and system timestamp."""

    id: int
    updated_at: datetime
