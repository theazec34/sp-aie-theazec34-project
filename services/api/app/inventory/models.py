"""SQLModel ORM tables for Brasaland inventory (CONTEXT hito backend).

Entity names match CONTEXT exactly. `current_stock` is never a column —
it is computed in schemas/services from entries − exits.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Ingredient(SQLModel, table=True):
    __tablename__ = "ingredient"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    unit: str
    category: str = Field(index=True)
    country: str = Field(index=True)

    entries: list["IngredientEntry"] = Relationship(back_populates="ingredient")
    exits: list["IngredientExit"] = Relationship(back_populates="ingredient")


class IngredientEntry(SQLModel, table=True):
    """Inbound delivery from a supplier (README: InboundOrder)."""

    __tablename__ = "ingredient_entry"

    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", index=True)
    quantity: float
    supplier_name: str
    location_id: int  # 1–14; validated in request schemas (not a FK)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    # TinyDB user id as string (numeric id, e.g. "1") — not a Supabase UUID.
    user_uuid: str

    ingredient: Optional[Ingredient] = Relationship(back_populates="entries")


class IngredientExit(SQLModel, table=True):
    """Consumption or waste (README: OutboundOrder)."""

    __tablename__ = "ingredient_exit"

    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", index=True)
    quantity: float
    reason: str  # "consumption" | "waste" — validated in schemas
    location_id: int  # 1–14; validated in request schemas (not a FK)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    # TinyDB user id as string (numeric id, e.g. "1") — not a Supabase UUID.
    user_uuid: str

    ingredient: Optional[Ingredient] = Relationship(back_populates="exits")
