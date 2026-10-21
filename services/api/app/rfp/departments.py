"""Departamentos RFP — reexporta la fuente única del pipeline (BRIEFING)."""

from __future__ import annotations

import sys
from pathlib import Path

# Local:  services/api/app/rfp/… → repo root (parents[4])
# Docker: /app/api/app/rfp/… → /app (parents[3]) where data/ is mounted/copied
_HERE = Path(__file__).resolve()
for _candidate in (_HERE.parents[3], _HERE.parents[4]):
    if (_candidate / "data" / "pipelines").is_dir():
        _root = str(_candidate)
        if _root not in sys.path:
            sys.path.insert(0, _root)
        break

from data.pipelines.rfp_intake.departments_ref import (  # noqa: E402, F401
    DEPARTMENTS,
    KNOWN_DEPARTMENT_IDS,
    DepartmentInfo,
    normalize_departments,
    resolve_unknown_department,
)
