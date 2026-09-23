# Technical Context — Brasaland Digital (actualizado 2026-09-23)

## Runtime
- **Website** `uis/website` — Next.js 16, puerto **3000**
- **Backoffice** `uis/backoffice` — Next.js 16, puerto **3001**
- **API** `services/api` — FastAPI/uvicorn, puerto **8000** (`/docs`)
- **Redis / Celery / Flower** — broker `:6379`, Flower `:5555` (DEV-55)
- **Qdrant** — `:6333` (RAG)
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

## ML — predicción de ventas Brasaland
- CONTEXT: `CONTEXT-brasaland.es.md`
- Datos: `data/raw/brasaland_sales.csv`
- Train: `scripts/train_sales_forecast.py` → `models/brasaland_sales_forecast.joblib`
- Paquete: `scripts/sales_forecast/` (data + metrics)
- Salidas train: `data/forecast/` (report, metrics, prediction_band)
- Eval técnica (hito posterior): `scripts/evaluate_revenue_model.py` → `data/eval/`
- Tests: `tests/pipelines/test_sales_forecast_split.py`, `test_temporal_cv.py`
- Deps: `uv` (`pyproject.toml`)


## Celery / Redis (DEV-55)
- App: `services/celery_app.py` · tasks: `services/tasks/`
- Broker/backend: `REDIS_URL` (Compose: `redis://redis:6379/0`)
- Analyze async: `POST /api/v1/incidents/analyze` → 202 `{task_id}`
- Status: `GET /tasks/{task_id}` · DLQ: `celery_dead_letters`
- Flower: `:5555` · worker proceso independiente
- Docs: `docs/async-tasks/DEV-55.md`

## LangGraph agent (Part 2 — external tools)
- Tools: `services/agent/tools/` (tickets + inventario, read-only, timeout)
- Routing: `classify_intent` → rag | ticket | inventory
- Fallback: `tool_fallback` (sin alucinar estado/stock)
- Docs: `docs/agent/langgraph-external-tools.md`
- Evals: `tests/pipelines/test_agent_tools.py`

## LangGraph agent (Part 1)
- Paquete: `services/agent/` (grafo compilado + checkpoint MemorySaver)
- Nodos separados: receive → retrieve → generate | refuse
- API: `POST /agent/query`, `GET /agent/traces/{run_id}`
- Traces: `data/eval/agent_traces/`
- Evals: `tests/pipelines/test_agent_graph.py`
- Docs: `docs/agent/langgraph-agent-base.md`

## RAG — Base de conocimiento Brasaland
- CONTEXT: `docs/rag/CONTEXT-brasaland.es.md`
- Corpus: `docs/company-knowledge-base/`
- Index: `data/process/rag.py` (`setup`, `embed`) → Qdrant `brasaland_knowledge`
- Pipeline: `data/pipelines/rag.py` (`retrieve`, `generate_answer`, `query`)
- API: `POST /knowledge/query` (`services/knowledge/`)
- UI: backoffice `/knowledge`
- Eval: `data/eval/test-queries.json` + `scripts/eval_rag_recall.py`
- Diseño: `docs/rag/rag-design.md`
- Infra: servicio `qdrant` en `docker-compose.yml` (`:6333`)

## Rama / PRs mergeados (ML & data)
- Pipeline resiliente: mergeado (#28)
- Subflows + dashboard: mergeado (#29)
- Script nocturno: mergeado (#30)
- Sentimiento WeLoveReviews: mergeado (#31)
- Eval regresión ventas: mergeado (#32)
- Forecast ventas (train): mergeado (#33)
- RAG knowledge base: mergeado (#35)
- Celery DEV-55: mergeado (#36)
- LangGraph agent base: rama `feature/langgraph-agent-base`
- Producto estable: **`main`**
