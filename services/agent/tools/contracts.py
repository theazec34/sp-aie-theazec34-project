"""Typed contracts for agent external tools (Part 2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TicketLookupInput(BaseModel):
    """Input for the support-ticket lookup tool (read-only)."""

    ticket_id: int | None = Field(
        default=None,
        description="Numeric incident id from the question, if present",
    )
    status: str | None = Field(
        default=None,
        description="Optional status filter (open, in_progress, resolved, discarded)",
    )
    category: str | None = None
    origin: str | None = None
    branch: str | None = None
    limit: int = Field(default=5, ge=1, le=50)


class TicketRecord(BaseModel):
    """Output fields aligned with GET /api/incidents Incident schema."""

    id: int
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: datetime
    updated_at: datetime


class TicketLookupOutput(BaseModel):
    ok: bool
    source: Literal["incidents"] = "incidents"
    tickets: list[TicketRecord] = Field(default_factory=list)
    error: str | None = None
    timed_out: bool = False


class InventoryLookupInput(BaseModel):
    """Input for inventory stock lookup (read-only)."""

    product_id: int | None = None
    name_query: str | None = Field(
        default=None,
        description="Substring to match ingredient name / sku",
    )
    limit: int = Field(default=10, ge=1, le=50)


class InventoryProductRecord(BaseModel):
    """Aligned with GET /inventory/products IngredientRead."""

    id: int
    name: str
    sku: str
    unit: str
    category: str
    country: str
    current_stock: float


class InventoryLookupOutput(BaseModel):
    ok: bool
    source: Literal["inventory"] = "inventory"
    products: list[InventoryProductRecord] = Field(default_factory=list)
    error: str | None = None
    timed_out: bool = False
