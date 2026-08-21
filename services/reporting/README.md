# `services/reporting/` — Business performance API (design stub)

This module exposes **business KPIs** for Brasaland leadership. It is intentionally
separate from `services/telemetry/` (engineering / technical report).

## Planned endpoints (see `data/pipelines/PIPELINE_DESIGN.md` Fase 5)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/reporting/weekly-location-performance` | Weekly cost & waste KPIs per location |
| `GET` | `/reporting/pipeline-runs/latest` | Latest pipeline run status |
| `POST` | `/reporting/pipeline-runs` | Manual / backfill trigger |

## Rules

- **No ETL logic here.** Routers import orchestration helpers from `data/pipelines/`.
- **Never write** to `telemetry_events`.
- Destination tables live under schema `reporting` (SQL:
  `services/api/sql/reporting_weekly_location_performance.sql`).

## Status

Design-only in the `pipeline-design` hito. Implementation comes in a later
Prefect + reporting milestone.
