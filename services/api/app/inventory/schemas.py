"""Pydantic request/response schemas for inventory (separate from ORM).

Never return SQLModel table instances from the API — always map to these.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

IngredientCategory = Literal[
    "meat", "produce", "sauce", "beverage", "packaging", "cleaning"
]
IngredientCountry = Literal["CO", "US"]
IngredientUnit = Literal["kg", "litro", "unidad"]
ExitReason = Literal["consumption", "waste"]
OrderKind = Literal["inbound", "outbound"]


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    unit: IngredientUnit
    category: IngredientCategory
    country: IngredientCountry


class IngredientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    unit: str
    category: str
    country: str
    current_stock: float


class IngredientEntryCreate(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    supplier_name: str = Field(min_length=1)
    location_id: int = Field(ge=1, le=14)


class IngredientEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    supplier_name: str
    location_id: int
    created_at: datetime
    user_uuid: str


class IngredientExitCreate(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    reason: ExitReason
    location_id: int = Field(ge=1, le=14)

    @field_validator("reason")
    @classmethod
    def reason_allowed(cls, value: str) -> str:
        if value not in {"consumption", "waste"}:
            raise ValueError("reason must be 'consumption' or 'waste'")
        return value


class IngredientExitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    reason: str
    location_id: int
    created_at: datetime
    user_uuid: str


class IngredientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    unit: str
    category: str
    country: str


class OrderRead(BaseModel):
    """Unified row for GET /inventory/orders (inbound or outbound)."""

    kind: OrderKind
    id: int
    ingredient_id: int
    quantity: float
    location_id: int
    created_at: datetime
    user_uuid: str
    supplier_name: str | None = None
    reason: str | None = None
    ingredient: IngredientBrief
