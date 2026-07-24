"""Map legacy CSV rows to the centralized Incident model (CONTEXT)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .csv_rules import detect_violations

STATUS_FROM_CSV = {
    "OPEN": "open",
    "CLOSED": "resolved",
    "DISCARDED": "discarded",
}

CATEGORY_FROM_CSV = {
    "CUSTOMER_COMPLAINT": "customer_complaint",
    "EQUIPMENT": "equipment_failure",
    "SUPPLY": "supply_issue",
    "FOOD_QUALITY": "customer_complaint",
    "STAFF": "staff_issue",
}

BRANCH_FROM_LOCATION = {
    "COL-01": "medellin_centro",
    "COL-02": "medellin_laureles",
    "COL-03": "medellin_envigado",
    "COL-04": "medellin_bello",
    "COL-05": "medellin_itagui",
    "COL-06": "bogota_chapinero",
    "COL-07": "bogota_usaquen",
    "COL-08": "cali_granada",
    "COL-09": "barranquilla_norte",
    "COL-10": "central",
    "FLA-01": "miami_doral",
    "FLA-02": "miami_hialeah",
    "FLA-03": "miami_kendall",
    "FLA-04": "orlando_international",
}


@dataclass
class MappedIncident:
    source_key: str
    title: str
    description: str
    category: str
    status: str
    origin: str
    branch: str
    created_at: datetime


def map_csv_row(row: dict[str, str]) -> tuple[MappedIncident | None, str | None]:
    """
    Validate with analyzer rules, then map to gestor fields.

    Returns (mapped, None) on success, or (None, reason) if discarded.
    """
    violations = detect_violations(row)
    if violations:
        return None, f"reglas CSV: {', '.join(violations)}"

    description = (row.get("description") or "").strip()
    title = description[:120].strip()
    if not title:
        return None, "title vacío tras recortar description"

    csv_status = (row.get("status") or "").strip()
    status = STATUS_FROM_CSV.get(csv_status)
    if status is None:
        return None, f"status CSV no mapeable: {csv_status!r}"

    csv_category = (row.get("category") or "").strip()
    category = CATEGORY_FROM_CSV.get(csv_category)
    if category is None:
        return None, f"category CSV no mapeable: {csv_category!r}"

    location_id = (row.get("location_id") or "").strip()
    branch = BRANCH_FROM_LOCATION.get(location_id, "central")

    date_raw = (row.get("date") or "").strip()
    try:
        created_at = datetime.strptime(date_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None, f"date inválida: {date_raw!r}"

    incident_id = (row.get("incident_id") or row.get("ticket_id") or "").strip()
    if incident_id:
        source_key = incident_id
    else:
        source_key = f"{title}|{created_at.date().isoformat()}"

    return (
        MappedIncident(
            source_key=source_key,
            title=title,
            description=description,
            category=category,
            status=status,
            origin="customer",
            branch=branch,
            created_at=created_at,
        ),
        None,
    )
