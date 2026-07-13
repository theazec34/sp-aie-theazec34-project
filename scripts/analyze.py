#!/usr/bin/env python3
"""CLI wrapper for Brasaland incident CSV analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.analyzer import (  # noqa: E402
    VALID_CATEGORIES,
    VALID_STATUSES,
    analyze_file,
    build_export_rows,
    export_to_csv_text,
    pct,
)


def print_report(result) -> None:
    from collections import Counter

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


def export_results(result, output_path: Path) -> None:
    output_path.write_text(export_to_csv_text(result), encoding="utf-8")
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
