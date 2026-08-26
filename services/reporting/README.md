# `services/reporting/` — Business performance API

Exposes **business KPIs** for Brasaland leadership. Separate from
`services/telemetry/` (engineering report).

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/reporting/weekly-location-performance` | Weekly cost & waste KPIs per location |
| `GET` | `/reporting/pipeline-runs/latest` | Latest pipeline run metadata |
| `POST` | `/reporting/pipeline-runs` | Manual / backfill trigger |

All routes require JWT (`Authorization: Bearer …`), same as other protected API routes.

## Rules

- **No ETL logic here.** Routers import `data/pipelines/pipeline.py` and DB helpers.
- **Never write** to `telemetry_events`.
- Destination: `reporting.weekly_location_performance` (see SQL under `services/api/sql/`).

## Run the pipeline locally

```bash
python data/pipelines/pipeline.py
```
