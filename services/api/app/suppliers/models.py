"""Pydantic models for Brasaland supplier directory (CONTEXT exact fields)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


class Country(str, Enum):
    COLOMBIA = "Colombia"
    USA = "USA"


class Currency(str, Enum):
    COP = "COP"
    USD = "USD"


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
COUNTRY_CURRENCY = {
    Country.COLOMBIA: Currency.COP,
    Country.USA: Currency.USD,
}

PositiveRate = Annotated[float, Field(gt=0, description="Tarifa vigente por unidad (> 0)")]


class SupplierBase(BaseModel):
    name: str = Field(min_length=1)
    country: Country
    categories: list[ProductCategory] = Field(min_length=1)
    rate_per_unit: PositiveRate
    currency: Currency
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

    @model_validator(mode="after")
    def currency_matches_country(self) -> SupplierBase:
        expected = COUNTRY_CURRENCY[self.country]
        if self.currency != expected:
            raise ValueError(
                f"currency must be {expected.value} when country is {self.country.value}"
            )
        return self


class SupplierCreate(SupplierBase):
    """Input model for POST /suppliers — no id or updated_at from client."""


class SupplierRateUpdate(BaseModel):
    rate_per_unit: PositiveRate


class SupplierStatusUpdate(BaseModel):
    status: SupplierStatus


class Supplier(SupplierBase):
    """Response model including TinyDB document id and system timestamp."""

    id: int
    updated_at: datetime
