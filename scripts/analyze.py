#!/usr/bin/env python3
"""Analyze Brasaland incident CSV reports (validation + metrics)."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

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


def analyze_file(path: Path) -> AnalysisResult:
    result = AnalysisResult(source_file=path.name)

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            result.total_records += 1
            violations = detect_violations(row)
            if violations:
                for rule in violations:
                    result.rule_counts[rule] += 1
            else:
                result.valid_records.append(row)

    return result


def pct(part: int, whole: int) -> str:
    if whole == 0:
        return "0.0%"
    return f"{(part / whole) * 100:.1f}%"


def print_report(result: AnalysisResult) -> None:
    valid = result.valid_records
    valid_count = len(valid)

    category_counts = Counter(row["category"] for row in valid)
    status_counts = Counter(row["status"] for row in valid)

    closed_records = [row for row in valid if row["status"] == "CLOSED"]
    score_counts = Counter()
    score_sum = 0
    for row in closed_records:
        score = int(row["satisfaction_score"])
        score_counts[score] += 1
        score_sum += score

    closed_count = len(closed_records)
    average_score = score_sum / closed_count if closed_count else 0.0

    print("=" * 60)
    print("  BRASALAND — INCIDENT REPORT ANALYSIS")
    print(f"  Source file: {result.source_file}")
    print("=" * 60)
    print()
    print(f"TOTAL RECORDS IN FILE .......... {result.total_records}")
    print(f"  ├─ Valid records ................ {valid_count}")
    print(f"  └─ Invalid / incomplete .......... {result.invalid_count}")
    print()
    print("INVALID RECORDS BREAKDOWN")
    print(
        "  ├─ Missing location_id ........... "
        f"{result.rule_counts['missing_location_id']}"
    )
    print(
        "  ├─ Invalid or missing category ... "
        f"{result.rule_counts['invalid_category']}"
    )
    print(
        "  ├─ Empty description ............. "
        f"{result.rule_counts['empty_description']}"
    )
    print(
        "  └─ Closed case, no score ......... "
        f"{result.rule_counts['closed_no_score']}"
    )
    print()
    print("BREAKDOWN BY CATEGORY (valid records)")
    for index, category in enumerate(VALID_CATEGORIES):
        count = category_counts.get(category, 0)
        branch = "└─" if index == len(VALID_CATEGORIES) - 1 else "├─"
        print(
            f"  {branch} {category.ljust(18)} {count:>3}  ({pct(count, valid_count)})"
        )
    print()
    print("BREAKDOWN BY STATUS (valid records)")
    for index, status in enumerate(VALID_STATUSES):
        count = status_counts.get(status, 0)
        branch = "└─" if index == len(VALID_STATUSES) - 1 else "├─"
        print(
            f"  {branch} {status.ljust(18)} {count:>3}  ({pct(count, valid_count)})"
        )
    print()
    print("SATISFACTION INDEX (closed cases)")
    print(f"  Scored cases: {closed_count} of {closed_count}")
    print(f"  Average score: {average_score:.2f} / 5.00")
    score_labels = {
        1: "Score 1 (Very dissatisfied)",
        2: "Score 2 (Dissatisfied)",
        3: "Score 3 (Neutral)",
        4: "Score 4 (Satisfied)",
        5: "Score 5 (Very satisfied)",
    }
    for score in range(1, 6):
        count = score_counts.get(score, 0)
        branch = "└─" if score == 5 else "├─"
        print(f"  {branch} {score_labels[score]} ... {count}")
    print()
    print("=" * 60)
    print("Export results to CSV? [y / n]:")


def build_export_rows(result: AnalysisResult) -> list[dict[str, str]]:
    valid = result.valid_records
    valid_count = len(valid)
    category_counts = Counter(row["category"] for row in valid)
    status_counts = Counter(row["status"] for row in valid)

    closed_records = [row for row in valid if row["status"] == "CLOSED"]
    score_counts = Counter(int(row["satisfaction_score"]) for row in closed_records)
    closed_count = len(closed_records)
    average_score = (
        sum(score_counts[score] * score for score in score_counts) / closed_count
        if closed_count
        else 0.0
    )

    rows: list[dict[str, str]] = [
        {"metric": "total_records", "value": str(result.total_records), "percentage": ""},
        {"metric": "valid_records", "value": str(valid_count), "percentage": ""},
        {
            "metric": "invalid_records",
            "value": str(result.invalid_count),
            "percentage": "",
        },
    ]

    for rule_key, label in RULE_LABELS.items():
        rows.append(
            {
                "metric": f"invalid_{rule_key}",
                "value": str(result.rule_counts[rule_key]),
                "percentage": "",
            }
        )

    for category in VALID_CATEGORIES:
        count = category_counts.get(category, 0)
        rows.append(
            {
                "metric": f"category_{category.lower()}",
                "value": str(count),
                "percentage": pct(count, valid_count),
            }
        )

    for status in VALID_STATUSES:
        count = status_counts.get(status, 0)
        rows.append(
            {
                "metric": f"status_{status.lower()}",
                "value": str(count),
                "percentage": pct(count, valid_count),
            }
        )

    rows.append(
        {
            "metric": "satisfaction_scored_cases",
            "value": str(closed_count),
            "percentage": "",
        }
    )
    rows.append(
        {
            "metric": "satisfaction_average",
            "value": f"{average_score:.2f}",
            "percentage": "",
        }
    )

    for score in range(1, 6):
        count = score_counts.get(score, 0)
        rows.append(
            {
                "metric": f"satisfaction_score_{score}",
                "value": str(count),
                "percentage": "",
            }
        )

    return rows


def export_results(result: AnalysisResult, output_path: Path) -> None:
    rows = build_export_rows(result)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value", "percentage"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported to {output_path}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <incidents.csv>", file=sys.stderr)
        return 1

    source = Path(sys.argv[1])
    if not source.is_file():
        print(f"File not found: {source}", file=sys.stderr)
        return 1

    result = analyze_file(source)
    print_report(result)

    try:
        answer = input().strip().lower()
    except EOFError:
        answer = "n"

    if answer in {"y", "yes", "s", "si", "sí"}:
        output_path = source.with_name(f"{source.stem}-analysis.csv")
        export_results(result, output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
