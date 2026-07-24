"""Incident domain models for the centralized manager (CONTEXT exact values)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISCARDED = "discarded"


class IncidentOrigin(str, Enum):
    CUSTOMER = "customer"
    BRANCH = "branch"
    INTERNAL = "internal"


class IncidentCategory(str, Enum):
    EQUIPMENT_FAILURE = "equipment_failure"
    SUPPLY_ISSUE = "supply_issue"
    CUSTOMER_COMPLAINT = "customer_complaint"
    STAFF_ISSUE = "staff_issue"
    FACILITY_ISSUE = "facility_issue"
    POS_SYSTEM = "pos_system"
    DELIVERY_ISSUE = "delivery_issue"
    OTHER = "other"


class IncidentBranch(str, Enum):
    CENTRAL = "central"
    MEDELLIN_CENTRO = "medellin_centro"
    MEDELLIN_LAURELES = "medellin_laureles"
    MEDELLIN_ENVIGADO = "medellin_envigado"
    MEDELLIN_BELLO = "medellin_bello"
    MEDELLIN_ITAGUI = "medellin_itagui"
    BOGOTA_CHAPINERO = "bogota_chapinero"
    BOGOTA_USAQUEN = "bogota_usaquen"
    CALI_GRANADA = "cali_granada"
    BARRANQUILLA_NORTE = "barranquilla_norte"
    MIAMI_DORAL = "miami_doral"
    MIAMI_HIALEAH = "miami_hialeah"
    MIAMI_KENDALL = "miami_kendall"
    ORLANDO_INTERNATIONAL = "orlando_international"
    FORT_LAUDERDALE = "fort_lauderdale"


BRANCH_LABELS: dict[str, str] = {
    IncidentBranch.CENTRAL.value: "Central (Medellín / Miami)",
    IncidentBranch.MEDELLIN_CENTRO.value: "Medellín Centro",
    IncidentBranch.MEDELLIN_LAURELES.value: "Medellín Laureles",
    IncidentBranch.MEDELLIN_ENVIGADO.value: "Medellín Envigado",
    IncidentBranch.MEDELLIN_BELLO.value: "Medellín Bello",
    IncidentBranch.MEDELLIN_ITAGUI.value: "Medellín Itagüí",
    IncidentBranch.BOGOTA_CHAPINERO.value: "Bogotá Chapinero",
    IncidentBranch.BOGOTA_USAQUEN.value: "Bogotá Usaquén",
    IncidentBranch.CALI_GRANADA.value: "Cali Granada",
    IncidentBranch.BARRANQUILLA_NORTE.value: "Barranquilla Norte",
    IncidentBranch.MIAMI_DORAL.value: "Miami Doral",
    IncidentBranch.MIAMI_HIALEAH.value: "Miami Hialeah",
    IncidentBranch.MIAMI_KENDALL.value: "Miami Kendall",
    IncidentBranch.ORLANDO_INTERNATIONAL.value: "Orlando International Drive",
    IncidentBranch.FORT_LAUDERDALE.value: "Fort Lauderdale",
}

CATEGORY_LABELS: dict[str, str] = {
    IncidentCategory.EQUIPMENT_FAILURE.value: "Fallo de equipamiento",
    IncidentCategory.SUPPLY_ISSUE.value: "Problema de insumos",
    IncidentCategory.CUSTOMER_COMPLAINT.value: "Queja de cliente",
    IncidentCategory.STAFF_ISSUE.value: "Incidencia de personal",
    IncidentCategory.FACILITY_ISSUE.value: "Instalaciones",
    IncidentCategory.POS_SYSTEM.value: "Sistema de caja / TPV",
    IncidentCategory.DELIVERY_ISSUE.value: "Delivery",
    IncidentCategory.OTHER.value: "Otra",
}

STATUS_LABELS: dict[str, str] = {
    IncidentStatus.OPEN.value: "Abierta",
    IncidentStatus.IN_PROGRESS.value: "En progreso",
    IncidentStatus.RESOLVED.value: "Resuelta",
    IncidentStatus.DISCARDED.value: "Descartada",
}

ORIGIN_LABELS: dict[str, str] = {
    IncidentOrigin.CUSTOMER.value: "Cliente",
    IncidentOrigin.BRANCH.value: "Sede",
    IncidentOrigin.INTERNAL.value: "Interna",
}

# Ciclo de vida: estados finales sin salidas
ALLOWED_STATUS_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.OPEN: {IncidentStatus.IN_PROGRESS, IncidentStatus.DISCARDED},
    IncidentStatus.IN_PROGRESS: {IncidentStatus.RESOLVED, IncidentStatus.DISCARDED},
    IncidentStatus.RESOLVED: set(),
    IncidentStatus.DISCARDED: set(),
}

NonEmptyStr = Annotated[str, Field(min_length=1)]


class IncidentCreate(BaseModel):
    title: NonEmptyStr
    description: NonEmptyStr
    category: IncidentCategory
    origin: IncidentOrigin
    branch: IncidentBranch
    # status is always open on create (server-side default)


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class Incident(BaseModel):
    id: int
    title: str
    description: str
    category: IncidentCategory
    status: IncidentStatus
    origin: IncidentOrigin
    branch: IncidentBranch
    created_at: datetime
    updated_at: datetime


class IncidentSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_origin: dict[str, int]
    by_branch: dict[str, int]
