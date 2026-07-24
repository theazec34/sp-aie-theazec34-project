"""CSV validation rules from the incidents-file-analyzer (Brasaland)."""

from __future__ import annotations

VALID_LOCATIONS = {f"COL-{i:02d}" for i in range(1, 11)} | {
    f"FLA-{i:02d}" for i in range(1, 5)
}
VALID_CATEGORIES = (
    "CUSTOMER_COMPLAINT",
    "EQUIPMENT",
    "SUPPLY",
    "FOOD_QUALITY",
    "STAFF",
)
VALID_STATUSES = ("OPEN", "CLOSED", "DISCARDED")

RULE_LABELS = {
    "missing_location_id": "Missing location_id",
    "invalid_category": "Invalid or missing category",
    "empty_description": "Empty description",
    "missing_reporter_id": "Missing reporter_id",
    "closed_no_score": "Closed case, no score",
    "score_out_of_range": "Score out of range",
}


def parse_score(raw: str | None) -> int | None | str:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        return "invalid"


def detect_violations(row: dict[str, str]) -> list[str]:
    violations: list[str] = []

    location_id = (row.get("location_id") or "").strip()
    category = (row.get("category") or "").strip()
    description = (row.get("description") or "").strip()
    status = (row.get("status") or "").strip()
    reporter_id = (row.get("reporter_id") or "").strip()
    score = parse_score(row.get("satisfaction_score"))

    if not location_id or location_id not in VALID_LOCATIONS:
        violations.append("missing_location_id")

    if not category or category not in VALID_CATEGORIES:
        violations.append("invalid_category")

    if not description or len(description) < 5:
        violations.append("empty_description")

    if not reporter_id:
        violations.append("missing_reporter_id")

    if score == "invalid" or (
        isinstance(score, int) and (score < 1 or score > 5)
    ):
        violations.append("score_out_of_range")

    if status == "CLOSED" and score is None:
        violations.append("closed_no_score")

    return violations
