# Progress — Brasaland Digital

## Estado (2026-08-12)
- **Producto en `main`:** website + backoffice + API + Docker + Lighthouse + caching (PRs #1–#21 relevantes mergeados).
- **Limpieza** (`cursor/project-cleanup-docs-c620`):
  - Eliminado sitio estático raíz + `Imagenes/` PNG (~19 MB)
  - Eliminados dumps Lighthouse HTML/JSON (~10 MB); se conservan PNG + `AUDIT.md`/`REPORT.md`
  - Eliminados tipos Election, `esbuild`/demo-browser, CSV duplicado, SVGs basura, logs/bak
  - Playwright retarget a `uis/website`
  - Docs: `PROJECT.md` + README/memory-bank actualizados

## Hitos en main (resumen)
| Área | Entrega |
|------|---------|
| Web Next | `uis/website` |
| Backoffice | auth, proveedores, incidencias, inventario |
| API | JWT, TinyDB + SQLModel, cache TTL |
| CSV | `scripts/analyze.py`, `uis/web` en `:8000/` |
| Calidad | TESTING, error-handling, Lighthouse, caching |
| Infra | `docker-compose.yml`, `DOCKER.md` |

## No mergeado (consciente)
- `hito-3-talent-pipeline-tracker` / `3.5`
- `brasaland_agent`

## Cómo arrancar
Ver `PROJECT.md` §2 (puertos 3000 / 3001 / 8000) o `DOCKER.md`.

## Hito Telemetría (rama `telemetria`) — diseño
- CONTEXT: `docs/telemetry/CONTEXT-brasaland.es.telemetria.md`
- Plan: `docs/telemetry/telemetry-plan.md` (18 eventos: 6 obligatorios + 12 oportunidades)
- Schemas: `docs/telemetry/event-schemas.json` (draft-07)
- Solo diseño (sin instrumentación de código en este PR)
- PR título exigido: `docs: telemetry design plan`

## Hito Telemetría — Captura (rama `cursor/telemetry-capture-c620`)
- Stub `POST /telemetry/events` + modelo `TelemetryEvent` (sin persistencia).
- `TelemetryService` en backoffice: cola, batch 10s/20, sendBeacon, retry backoff.
- Instrumentadas métricas obligatorias CONTEXT + capa técnica (auth, nav, errores, latency, web vitals).
- Env: `NEXT_PUBLIC_TELEMETRY_ENDPOINT` / `TELEMETRY_ENDPOINT`.
- Notas: `docs/telemetry/CAPTURE.md`.

## Hito Telemetría — Almacenamiento (rama `cursor/telemetry-storage-c620`)
- Tabla `telemetry_events` (8 cols + índices timestamp/event_type/GIN tags); SQL en `services/api/sql/telemetry_events.sql`.
- Endpoint real: validación por evento + bulk INSERT; respuesta `{ received, stored, rejected }`.
- `TelemetryEvent` y frontend sin cambios; tags con allowlist CONTEXT (sin PII).
- Notas: `docs/telemetry/STORAGE.md`.

## Hito Telemetría — Reporte técnico (rama `cursor/telemetry-report-c620`)
- Pipeline Pandas: `services/telemetry/analysis.py` (events_per_day, error_rate_by_type, auth_failure_rate, latency_by_route).
- `GET /telemetry/report` con ventana de fechas (default 7 días UTC) + cache TTL 60s.
- Dashboard mínimo backoffice: `/telemetry`.
- Seed: `services/api/seed_telemetry.py`.
- PR título exigido: `feat: telemetry report endpoint`.
- Notas: `docs/telemetry/REPORT.md`.

## Hito Pipeline de negocio — Diseño (rama `pipeline-design`)
- CONTEXT: `docs/pipelines/CONTEXT-brasaland.es.pipeline.md`
- Diseño: `data/pipelines/PIPELINE_DESIGN.md` (5 fases: estado, ETL, resiliencia, Prefect, reporting)
- Destino: `reporting.weekly_location_performance` (SQL en `services/api/sql/`)
- Stub módulo: `services/reporting/` (sin ETL)
- PR título: `docs: business performance pipeline design`
- Solo diseño (sin orquestación Prefect aún)

## Hito Pipeline resiliente — Implementación (`cursor/resilient-pipeline-c620`)
- Prefect flow `weekly_location_performance_flow` en `data/pipelines/pipeline.py`
- Tasks extract/transform/load + eval opcional (`return_state=True`), retries, cache 1h, UPSERT idempotente
- Endpoints: `GET/POST /reporting/*` en `services/reporting/router.py`
- CLI: `python data/pipelines/pipeline.py`
- Commit message exigido: `feat: implement resilient business performance pipeline`

## Hito Pipeline a producción — Subflows + tests + dashboard (`cursor/pipeline-subflows-dashboard-c620`)
- Subflows de dominio (extract/transform/load/eval) coordinados por el flow principal
- Tests unitarios aislados: `tests/pipelines/test_pipeline.py`
- Dashboard negocio: backoffice `/reporting` (5 KPIs CONTEXT)
- Commit exigido: `feat: refactor business performance pipeline into subflows, add unit tests, and add reporting dashboard`

## Hito Script nocturno de telemetría — DEV-53 (`cursor/nightly-export-c620`)
- Tabla `job_runs` (orquestación nocturna, distinta de `pipeline_run_log`); SQL en `services/api/sql/job_runs.sql`
- Servicio `services/job_runner/` — máquina de estados `pending` → `processing` → `completed` | `failed`
- Script independiente `scripts/nightly_export.py`: export CSV backup → subprocess pipeline → registro en `job_runs`
- Lock distribuido vía fila `processing`; idempotencia por `(job_name, target_date)`; override `TARGET_DATE`
- Cron ejemplo: `scripts/crontab.example` (`0 2 * * *` UTC)
- Tests: `tests/scripts/test_nightly_export.py`

## Hito WeLoveReviews — Análisis de sentimiento (`cursor/sentiment-reviews-c620`)
- Notebook narrativo: `src/explore.ipynb` (EDA → modelo → resultados → conclusiones, outputs ejecutados)
- Producción: `src/app.py` + `src/sentiment_analysis.py`
- Modelo fijado: `nlptown/bert-base-multilingual-uncased-sentiment` (sin pesos en repo)
- Datos: `data/raw/reviews.csv` (500 reseñas servicio) → `data/processed/reviews_with_sentiment.csv`
- Dependencias ML: `requirements.txt` (transformers, torch, pandas, jupyter)
- Prompt EDA: `PROMPT.es.md`
