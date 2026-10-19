"""Canonical department ids from brasaland-BRIEFING.es.md — do not invent others."""

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
        "role": "Términos de marca, exclusividad, co-branding, validez de la oferta. Dueña del ticket.",
    },
    "operaciones": {
        "department_id": "operaciones",
        "name": "Operaciones de Restaurante",
        "owner": "Felipe Guerrero",
        "role": "Viabilidad operativa: capacidad, montaje, costo operativo/evento.",
    },
    "procurement": {
        "department_id": "procurement",
        "name": "Procurement y Proveedores",
        "owner": "Lucía Fernández",
        "role": "Costo estimado de insumos y lead times de proveedores.",
    },
    "training": {
        "department_id": "training",
        "name": "Training y Estándares de Calidad",
        "owner": "Jake Morrison",
        "role": "Receta/estándar nuevo, tiempo de desarrollo y certificación.",
    },
}

KNOWN_DEPARTMENT_IDS = frozenset(DEPARTMENTS.keys())


def resolve_unknown_department(raw_id: str) -> str | None:
    """
    Design: unknown department names map to the closest BRIEFING id or None.

    We never invent a fifth department — route to marketing (ticket owner) as
    open_question instead of creating rogue workers.
    """
    key = (raw_id or "").strip().lower()
    if key in KNOWN_DEPARTMENT_IDS:
        return key
    aliases = {
        "ops": "operaciones",
        "operations": "operaciones",
        "compras": "procurement",
        "supply": "procurement",
        "calidad": "training",
        "brand": "marketing",
        "sales": "marketing",
        "ventas": "marketing",
    }
    return aliases.get(key)
