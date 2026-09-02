# Technical Context — Brasaland Digital (actualizado 2026-08-12)

## Runtime
- **Website** `uis/website` — Next.js 16, puerto **3000**
- **Backoffice** `uis/backoffice` — Next.js 16, puerto **3001**
- **API** `services/api` — FastAPI/uvicorn, puerto **8000** (`/docs`)
- **Docker:** `docker compose up` (ver `DOCKER.md`)
- **TS Hito 2:** `src/` — `npm run typecheck` / `npm run demo`
- **E2E:** Playwright → website `:3000` (`npm run test:e2e`)
- **API tests:** `cd services/api && uv run pytest`

## Persistencia
- TinyDB: auth, profiles, suppliers, incidents (gitignored bajo `services/api/data/`)
- SQLModel inventario: `DATABASE_URL` (Supabase) o SQLite fallback

## API (grupos)
- Auth/users/profiles · Suppliers · Incidents (`/api/incidents`, analyze/export) · Inventory (`/inventory/*`)
- Cache TTL: summary 30s, suppliers 60s (`app/cache.py`) + middleware `api.timing`

## Frontends
- Website: carta + galería lazy + formulario lazy
- Backoffice: JWT, proveedores, incidencias, inventario (`useAsyncResource`, `AuthenticatedShell`)
- `uis/web`: analizador CSV montado en API `/`

## Docs canónicos
- `PROJECT.md` — mapa completo
- `README.md`, `DOCKER.md`, `CACHING_REPORT.md`, `AUDIT.md`, `REPORT.md`, `TESTING.md`
- Contextos: `Brasaland.md`, `CONTEXT-brasaland.es.md`, `CONTEXT-incidents-centralized.es.md`, `05-backend-inventory-orm/`
- Telemetría (diseño): `docs/telemetry/telemetry-plan.md`, `event-schemas.json`

## Telemetría
- Diseño: `docs/telemetry/telemetry-plan.md`, `event-schemas.json`
- Captura: `uis/backoffice/src/services/telemetry.ts` (`track`)
- Almacenamiento: `POST /telemetry/events` → `telemetry_events` (bulk); SQL `services/api/sql/telemetry_events.sql`
- Reporte técnico: `services/telemetry/analysis.py` + `GET /telemetry/report` (cache 60s) + UI `/telemetry`
- Docs: `docs/telemetry/CAPTURE.md`, `STORAGE.md`, `REPORT.md`

## Pipeline de negocio
- Diseño: `data/pipelines/PIPELINE_DESIGN.md`
- Flow + subflows: `data/pipelines/pipeline.py`
- Destino: `reporting.weekly_location_performance`
- API: `services/reporting/router.py` → `/reporting/*`
- Dashboard: backoffice `/reporting`
- Tests: `tests/pipelines/test_pipeline.py`

## Orquestación nocturna (DEV-53)
- Script: `scripts/nightly_export.py` (proceso independiente, no FastAPI)
- Estado: `job_runs` (`services/job_runner/`, SQL `services/api/sql/job_runs.sql`)
- CSV backup: `data/raw/telemetry_YYYY-MM-DD.csv` (auditoría; pipeline lee DB)
- Cron ejemplo: `scripts/crontab.example` — `0 2 * * *` UTC
- Tests: `tests/scripts/test_nightly_export.py`

## ML — WeLoveReviews (sentimiento)
- Notebook: `src/explore.ipynb` · Script: `src/app.py` · Helpers: `src/sentiment_analysis.py`
- Modelo HF: `nlptown/bert-base-multilingual-uncased-sentiment` (carga única, sin pesos en git)
- Datos: `data/raw/reviews.csv` → `data/processed/reviews_with_sentiment.csv`
- Deps: `requirements.txt` (raíz, hito ML)

## Rama
- Pipeline resiliente: mergeado (#28)
- Subflows + dashboard: mergeado (#29)
- Script nocturno: `cursor/nightly-export-c620`
- Sentimiento WeLoveReviews: `cursor/sentiment-reviews-c620`
- Producto estable: **`main`**
