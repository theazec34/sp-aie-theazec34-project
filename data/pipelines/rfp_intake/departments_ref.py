"""Fuente única de departamentos del BRIEFING (pipeline + API).

El API reexporta este módulo para no duplicar ids/responsables.
"""

from __future__ import annotations

from typing import TypedDict


class DepartmentInfo(TypedDict):
    department_id: str
    name: str
    owner: str
    role: str


DEPARTMENTS: dict[str, DepartmentInfo] = {
    "marketing": {
        "department_id": "marketing",
        "name": "Marketing y Experiencia Digital",
        "owner": "Camila Ospina",
        "role": (
            "Términos de marca, exclusividad, co-branding, validez de la oferta. "
            "Dueña del ticket."
        ),
    },
    "operaciones": {
        "department_id": "operaciones",
        "name": "Operaciones de Restaurante",
        "owner": "Felipe Guerrero",
        "role": "Viabilidad operativa: capacidad, montaje, costo operativo/evento.",
    },
    "procurement": {
        "department_id": "procurement",
        "name": "Compras y Proveedores",
        "owner": "Lucía Fernández",
        "role": "Costo estimado de insumos y tiempos de entrega de proveedores.",
    },
    "training": {
        "department_id": "training",
        "name": "Formación y Estándares de Calidad",
        "owner": "Jake Morrison",
        "role": "Receta/estándar nuevo, tiempo de desarrollo y certificación.",
    },
}

KNOWN_DEPARTMENT_IDS = frozenset(DEPARTMENTS.keys())

_ALIASES = {
    "ops": "operaciones",
    "operations": "operaciones",
    "compras": "procurement",
    "supply": "procurement",
    "calidad": "training",
    "formacion": "training",
    "formación": "training",
    "brand": "marketing",
    "sales": "marketing",
    "ventas": "marketing",
}


def resolve_unknown_department(raw_id: str) -> str | None:
    """
    Mapea alias al id canónico del BRIEFING o None.

    Nunca inventa un quinto departamento: lo desconocido se escala a marketing.
    """
    key = (raw_id or "").strip().lower()
    if key in KNOWN_DEPARTMENT_IDS:
        return key
    return _ALIASES.get(key)


def normalize_departments(raw: list[str]) -> list[str]:
    """Filtra/alias a ids BRIEFING; marketing (dueña del ticket) siempre presente."""
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        resolved = resolve_unknown_department(item)
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        out.append(resolved)
    if "marketing" not in seen:
        out.insert(0, "marketing")
    return out
