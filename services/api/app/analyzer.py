"""Core incident CSV analysis logic shared by CLI and API."""

from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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


@dataclass
class AnalysisResult:
    source_file: str
    total_records: int = 0
    valid_records: list[dict[str, str]] = field(default_factory=list)
    rule_counts: Counter[str] = field(default_factory=Counter)

    @property
    def invalid_count(self) -> int:
        return self.total_records - len(self.valid_records)


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


def analyze_rows(rows: list[dict[str, str]], source_file: str) -> AnalysisResult:
    result = AnalysisResult(source_file=source_file)
    for row in rows:
        result.total_records += 1
        violations = detect_violations(row)
        if violations:
            for rule in violations:
                result.rule_counts[rule] += 1
        else:
            result.valid_records.append(row)
    return result


def analyze_text(content: str, source_file: str) -> AnalysisResult:
    reader = csv.DictReader(io.StringIO(content))
    return analyze_rows(list(reader), source_file)


def analyze_file(path: Path) -> AnalysisResult:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return analyze_rows(list(reader), path.name)


def pct(part: int, whole: int) -> str:
    if whole == 0:
        return "0.0%"
    return f"{(part / whole) * 100:.1f}%"


def pct_value(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 1)


def build_report(result: AnalysisResult) -> dict[str, Any]:
    valid = result.valid_records
    valid_count = len(valid)
    category_counts = Counter(row["category"] for row in valid)
    status_counts = Counter(row["status"] for row in valid)

    closed_records = [row for row in valid if row["status"] == "CLOSED"]
    score_counts = Counter(int(row["satisfaction_score"]) for row in closed_records)
    closed_count = len(closed_records)
    average_score = (
        sum(score * score_counts[score] for score in score_counts) / closed_count
        if closed_count
        else 0.0
    )

    return {
        "source_file": result.source_file,
        "total_records": result.total_records,
        "valid_records": valid_count,
        "invalid_records": result.invalid_count,
        "invalid_breakdown": {
            "missing_location_id": result.rule_counts["missing_location_id"],
            "invalid_category": result.rule_counts["invalid_category"],
            "empty_description": result.rule_counts["empty_description"],
            "closed_no_score": result.rule_counts["closed_no_score"],
            "missing_reporter_id": result.rule_counts["missing_reporter_id"],
            "score_out_of_range": result.rule_counts["score_out_of_range"],
        },
        "by_category": [
            {
                "category": category,
                "count": category_counts.get(category, 0),
                "percentage": pct_value(category_counts.get(category, 0), valid_count),
            }
            for category in VALID_CATEGORIES
        ],
        "by_status": [
            {
                "status": status,
                "count": status_counts.get(status, 0),
                "percentage": pct_value(status_counts.get(status, 0), valid_count),
            }
            for status in VALID_STATUSES
        ],
        "satisfaction": {
            "scored_cases": closed_count,
            "total_closed": closed_count,
            "average": round(average_score, 2),
            "distribution": [
                {"score": score, "count": score_counts.get(score, 0)}
                for score in range(1, 6)
            ],
        },
    }


def build_export_rows(result: AnalysisResult) -> list[dict[str, str]]:
    report = build_report(result)
    valid_count = report["valid_records"]

    rows: list[dict[str, str]] = [
        {"metric": "total_records", "value": str(report["total_records"]), "percentage": ""},
        {"metric": "valid_records", "value": str(valid_count), "percentage": ""},
        {
            "metric": "invalid_records",
            "value": str(report["invalid_records"]),
            "percentage": "",
        },
    ]

    for rule_key in RULE_LABELS:
        rows.append(
            {
                "metric": f"invalid_{rule_key}",
                "value": str(report["invalid_breakdown"][rule_key]),
                "percentage": "",
            }
        )

    for item in report["by_category"]:
        rows.append(
            {
                "metric": f"category_{item['category'].lower()}",
                "value": str(item["count"]),
                "percentage": pct(item["count"], valid_count),
            }
        )

    for item in report["by_status"]:
        rows.append(
            {
                "metric": f"status_{item['status'].lower()}",
                "value": str(item["count"]),
                "percentage": pct(item["count"], valid_count),
            }
        )

    satisfaction = report["satisfaction"]
    rows.append(
        {
            "metric": "satisfaction_scored_cases",
            "value": str(satisfaction["scored_cases"]),
            "percentage": "",
        }
    )
    rows.append(
        {
            "metric": "satisfaction_average",
            "value": f"{satisfaction['average']:.2f}",
            "percentage": "",
        }
    )

    for item in satisfaction["distribution"]:
        rows.append(
            {
                "metric": f"satisfaction_score_{item['score']}",
                "value": str(item["count"]),
                "percentage": "",
            }
        )

    return rows


def export_to_csv_text(result: AnalysisResult) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["metric", "value", "percentage"])
    writer.writeheader()
    writer.writerows(build_export_rows(result))
    return buffer.getvalue()
