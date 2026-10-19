"""Departamentos RFP — reexporta la fuente única del pipeline (BRIEFING)."""

from __future__ import annotations

import sys
from pathlib import Path

# Asegura import de `data.pipelines.*` cuando el CWD es services/api
_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from data.pipelines.rfp_intake.departments_ref import (  # noqa: E402, F401
    DEPARTMENTS,
    KNOWN_DEPARTMENT_IDS,
    DepartmentInfo,
    normalize_departments,
    resolve_unknown_department,
)
