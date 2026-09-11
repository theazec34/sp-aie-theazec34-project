# Progress — Brasaland Digital

## Estado (2026-09-11) — repaso de `main`
- **Producto en `main`:** tip `f73c913` (luego docs de este repaso). PRs **#1–#21** y **#23–#33** mergeados; **0 PRs abiertos**.
- **Verificación smoke (este repaso):**
  - Artefactos de todos los hitos presentes (web, API, telemetry, pipeline, nightly, sentimiento, forecast/eval).
  - `uv run pytest tests/pipelines` → **10 passed**
  - `uv run pytest tests/scripts` → **8 passed** (tras instalar deps API)
  - `cd services/api && uv run pytest` → **51 passed**
  - `npm run build` website + backoffice → OK (rutas `/telemetry`, `/reporting` presentes)
- **Fuera de alcance (consciente, no mergear sin PR dedicado):**
  - `hito-3-talent-pipeline-tracker` / `3.5`
  - `brasaland_agent`

## Hallazgos del repaso (no bloquean main)
| Tema | Detalle | Acción tomada / residual |
|------|---------|--------------------------|
| Docs desfasadas | README / mapa de carpetas sin ML·pipeline·telemetry | Actualizado en este PR |
| CONTEXT ventas duplicado | `CONTEXT-brasaland.es.md` ≡ `CONTEXT-brasaland-sales.es.md` | Alias → canónico |
| Alias joblib | `revenue_regressor.joblib` = copia de `brasaland_sales_forecast.joblib` | Se mantiene por compat eval legacy |
| Eval staging | Alto PSI (~5.8) + overfitting en learning curve | Documentado en `data/eval/`; no staging-ready |
| Tests sentimiento | Cubre notebook/script; poca automatización | Residual opcional |
| Root `pyproject.toml` | Solo deps ML/forecast; nightly/API necesitan `services/api/requirements.txt` | Documentado en PROJECT §9 |

## Hitos en main (resumen)
| Área | Entrega | PR |
|------|---------|-----|
| Web Next | `uis/website` | #1–3 |
| Backoffice | auth, proveedores, incidencias, inventario, `/telemetry`, `/reporting` | #9–18, #24–26, #29 |
| API | JWT, TinyDB + SQLModel, cache TTL, telemetry, reporting | #4–21, #24–29 |
| CSV | `scripts/analyze.py`, `uis/web` en `:8000/` | #5 |
| Telemetría | captura → `telemetry_events` → reporte | #23–#26 |
| Pipeline negocio | Prefect subflows + KPIs + dashboard | #27–#29 |
| Nightly DEV-53 | `nightly_export.py` + `job_runs` | #30 |
| Sentimiento | WeLoveReviews notebook + `src/app.py` | #31 |
| Ventas ML | eval TimeSeriesSplit (#32) + train XGBoost 8y/2y (#33) | #32–#33 |
| Calidad | TESTING, error-handling, Lighthouse, caching | #15–16, #20–21 |
| Infra | `docker-compose.yml`, `DOCKER.md` | #19 |
| Limpieza | monorepo ~28MB + PROJECT.md | #22 |

## Cómo arrancar
Ver `PROJECT.md` §2 (puertos 3000 / 3001 / 8000) o `DOCKER.md`.

## Detalle por hito (referencia)

### Telemetría
- Diseño: `docs/telemetry/telemetry-plan.md`, `event-schemas.json`
- Captura: `uis/backoffice/src/services/telemetry.ts`
- Storage: `POST /telemetry/events` → `telemetry_events`
- Reporte: `services/telemetry/analysis.py` + `GET /telemetry/report` + UI `/telemetry`

### Pipeline de negocio
- Diseño: `data/pipelines/PIPELINE_DESIGN.md`
- Flow + subflows: `data/pipelines/pipeline.py`
- API: `services/reporting/router.py` → `/reporting/*`
- Dashboard: backoffice `/reporting`
- Tests: `tests/pipelines/test_pipeline.py`

### Orquestación nocturna (DEV-53)
- `scripts/nightly_export.py` + `services/job_runner/` + SQL `job_runs`
- Cron: `scripts/crontab.example` — `0 2 * * *` UTC
- Tests: `tests/scripts/test_nightly_export.py`

### WeLoveReviews (sentimiento)
- `src/explore.ipynb`, `src/app.py`, `src/sentiment_analysis.py`
- Datos: `data/raw/reviews.csv` → `data/processed/reviews_with_sentiment.csv`
- Deps: `requirements.txt` (raíz)

### Predicción de ventas + evaluación
- CONTEXT: `CONTEXT-brasaland.es.md` (alias: `CONTEXT-brasaland-sales.es.md`)
- Datos: `data/raw/brasaland_sales.csv`
- Train: `scripts/train_sales_forecast.py` → `models/brasaland_sales_forecast.joblib` + `data/forecast/`
- Eval: `scripts/evaluate_revenue_model.py` → `data/eval/`
- Tests: `tests/pipelines/test_sales_forecast_split.py`, `test_temporal_cv.py`
- Deps: `uv` (`pyproject.toml`)
