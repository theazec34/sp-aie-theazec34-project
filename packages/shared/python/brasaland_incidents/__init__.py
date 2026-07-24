"""Shared Brasaland incident helpers (CSV rules + gestor mapping)."""

from .csv_rules import (
    RULE_LABELS,
    VALID_CATEGORIES,
    VALID_LOCATIONS,
    VALID_STATUSES,
    detect_violations,
    parse_score,
)
from .mapping import (
    BRANCH_FROM_LOCATION,
    CATEGORY_FROM_CSV,
    STATUS_FROM_CSV,
    MappedIncident,
    map_csv_row,
)

__all__ = [
    "BRANCH_FROM_LOCATION",
    "CATEGORY_FROM_CSV",
    "MappedIncident",
    "RULE_LABELS",
    "STATUS_FROM_CSV",
    "VALID_CATEGORIES",
    "VALID_LOCATIONS",
    "VALID_STATUSES",
    "detect_violations",
    "map_csv_row",
    "parse_score",
]
