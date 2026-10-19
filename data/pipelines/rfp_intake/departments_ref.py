"""Department constants mirrored from BRIEFING (pipeline-local, no FastAPI import)."""

from __future__ import annotations

DEPARTMENTS: dict[str, dict[str, str]] = {
    "marketing": {
        "department_id": "marketing",
        "name": "Marketing y Experiencia Digital",
        "owner": "Camila Ospina",
    },
    "operaciones": {
        "department_id": "operaciones",
        "name": "Operaciones de Restaurante",
        "owner": "Felipe Guerrero",
    },
    "procurement": {
        "department_id": "procurement",
        "name": "Procurement y Proveedores",
        "owner": "Lucía Fernández",
    },
    "training": {
        "department_id": "training",
        "name": "Training y Estándares de Calidad",
        "owner": "Jake Morrison",
    },
}
