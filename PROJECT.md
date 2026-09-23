# PROJECT — Mapa completo Brasaland Digital

Documento canónico del monorepo (actualizado 2026-09-11). Sustituye lecturas antiguas de README/memory-bank que hablaban del sitio estático o del dominio de “elecciones”.

---

## 1. Qué es este proyecto

**Brasaland** es un restaurante (cocina brasileña / alma ibérica) con:

1. **Sitio corporativo** — carta, galería, formulario.  
2. **Backoffice** — login JWT, proveedores, incidencias, inventario.  
3. **API** — FastAPI monolito modular (TinyDB + SQLModel).  

Objetivo académico/profesional: construir una plataforma digital operable (auth, CRUD, análisis, rendimiento, Docker), no solo una landing.

---

## 2. Arquitectura actual (puertos)

```text
Browser
  ├─ :3000  uis/website     Next.js 16 — público
  ├─ :3001  uis/backoffice  Next.js 16 — ops (JWT en localStorage)
  │            ├─ /telemetry   reporte técnico
  │            └─ /reporting   KPIs semanales por local
  └─ :8000  services/api    FastAPI
              ├─ /docs, /health, /auth, /users, /profiles
              ├─ /suppliers, /api/incidents*, /inventory/*
              ├─ /telemetry/*, /reporting/*
              └─ /  → uis/web (analizador CSV estático)

Jobs / ML (fuera del request path)
  ├─ scripts/nightly_export.py          → job_runs + pipeline Prefect
  ├─ scripts/train_sales_forecast.py    → models/*.joblib + data/forecast/
  ├─ scripts/evaluate_revenue_model.py  → data/eval/
  └─ src/app.py (WeLoveReviews)         → data/processed/reviews_with_sentiment.csv
```

| Puerto | Cómo abrirlo | Notas |
|--------|--------------|-------|
| **3000** | `cd uis/website && npm i && npm run dev` | En Docker: servicio `interfaces` |
| **3001** | `cd uis/backoffice && npm i && npm run dev` | Misma imagen Docker que 3000 |
| **8000** | `cd services/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | Docs: `/docs` |

**Docker (todo junto):**

```bash
cp .env.example .env
docker compose up --build
```

Detalle: [DOCKER.md](./DOCKER.md).

**Variables clave**

- `NEXT_PUBLIC_API_URL=http://localhost:8000` (navegador → API)  
- `SECRET_KEY`, `DATABASE_URL` (opcional Supabase; si falla → SQLite)  
- Resend opcionales para reset de contraseña  

---

## 3. Capas y datos

| Persistencia | Qué guarda |
|--------------|------------|
| TinyDB (`services/api/data/`, gitignored) | Users, profiles, suppliers, incidents, reset tokens |
| SQLModel | Ingredients, entries, exits (`DATABASE_URL` o SQLite local) |

**Seeds**

| Script | Contenido |
|--------|-----------|
| `seed_auth.py` | Admin |
| `seed.py` | Proveedores CONTEXT |
| `seed_inventory.py` | Ingredientes + movimientos |
| `seed_load.py` | Carga pesada para cache/latency (~800 incidencias) |
| `scripts/seed_incidents.py` | CSV → incidencias |

CSV de prueba: `incidents-brasaland.csv` (raíz).

---

## 4. Hitos mergeados en `main` (producto)

PRs **MERGED** en `main` (actualizado 2026-09-11):

| # | Hito | Aporta |
|---|------|--------|
| 1–3 | Web + Hito 4 / actualización | Base Brasaland, memoria, skills |
| 4 | Arquitectura backend | `docs/architecture_proposal.md` |
| 5 | CSV postventa | `scripts/analyze.py`, `uis/web`, API analyze/export |
| 6–8 | Progress / CORS Codespaces / UI en :8000 | DX Codespaces |
| 9 | Proveedores | CRUD TinyDB + backoffice |
| 10 | Users & profiles | Registro, `/auth/me`, perfil |
| 11 | Funcionamiento total | Integración auth + UI |
| 12–13 | Auth Failed to fetch + recuperación password | URL API editable, forgot/reset/change |
| 14 | Incidencias centralizadas | `/api/incidents` + UI |
| 15 | Error-handling audit | Errores coherentes FE/BE |
| 16 | Testing | `TESTING.md`, pytest, Jest |
| 17–18 | Inventario ORM + UI | SQLModel + pantallas stock/órdenes |
| 19 | Docker | Compose website+backoffice+API |
| 20 | Performance Lighthouse | `AUDIT.md`, `REPORT.md`, `audit/*` PNG |
| 21 | Caching | TTL summary/suppliers, lazy/useMemo, `CACHING_REPORT.md` |
| 23 | Telemetría diseño | `docs/telemetry/telemetry-plan.md`, schemas |
| 24 | Telemetría captura | `TelemetryService` + instrumentación backoffice |
| 25 | Telemetría almacenamiento | `telemetry_events` bulk insert |
| 26 | Telemetría reporte | `GET /telemetry/report` + UI `/telemetry` |
| 27 | Pipeline diseño | `data/pipelines/PIPELINE_DESIGN.md` |
| 28 | Pipeline resiliente | Prefect flow + UPSERT KPIs |
| 29 | Pipeline subflows + dashboard | Tests + UI `/reporting` |
| 30 | Script nocturno DEV-53 | `nightly_export.py` + `job_runs` |
| 31 | WeLoveReviews sentimiento | `src/explore.ipynb` + `src/app.py` |
| 32 | Eval modelo ventas | TimeSeriesSplit + learning curve (`data/eval/`) |
| 33 | Forecast ventas (train) | XGBoost 8y/2y (`data/forecast/`, `train_sales_forecast.py`) |
| 34 | Project review docs | Sync mapa hitos + README |
| 35 | RAG knowledge base | Qdrant `brasaland_knowledge` + `/knowledge` |
| 36 | Celery DEV-55 | Redis + worker + Flower; analyze → 202/`task_id` |
| — | LangGraph agent base (este PR) | Grafo retrieve/generate + `/agent/query` |

### Ramas remotas **no** mergeadas (fuera del producto principal)

| Rama | Contenido | Por qué no está en main |
|------|-----------|-------------------------|
| `hito-3-talent-pipeline-tracker` / `3.5` | App Next “Talent Pipeline” en `apps/` | Hito académico paralelo, no es ops Brasaland |
| `brasaland_agent` | Agente TS + memoria | Experimento; no forma parte del runtime Docker |

Si quieres fusionar Talent Pipeline o el Agent, hacerlo en PRs dedicados (añaden mucho código ajeno al stack actual).

---

## 5. Puntos fuertes

1. **Monorepo operable de punta a punta** — tres superficies + API real, no mocks.  
2. **Auth completa** — register/login/JWT, perfil, forgot/reset/change password.  
3. **Dominios de negocio claros** — proveedores, incidencias (CSV + CRUD), inventario con stock calculado.  
4. **Dual DB pragmática** — TinyDB para ops ligeras; SQLModel para inventario (Supabase o SQLite).  
5. **Observabilidad** — telemetría captura→storage→reporte + pipeline Prefect + nightly `job_runs`.  
6. **ML aplicado** — sentimiento reseñas + forecast/eval de ventas con split temporal y métricas de negocio.  
7. **Rendimiento documentado** — Lighthouse before/after + cache TTL con invalidación y informe.  
8. **Docker one-shot** — `compose up` con fallback si Supabase no responde.  
9. **Tests** — pytest API/pipelines/nightly/forecast, Jest backoffice, Playwright website.  
10. **Dominio TS Brasaland en `src/`** — EncargoProveedor / PlatoCarta / ReservaMesa / PedidoDomicilio + reportes.

---

## 6. Mapa de carpetas (qué importa)

```text
uis/website/          # CANÓNICO sitio público
uis/backoffice/       # CANÓNICO panel ops (+ /telemetry, /reporting)
uis/web/              # UI CSV servida por API
services/api/         # CANÓNICO backend (+ telemetry SQL, job_runs SQL)
services/telemetry/   # análisis Pandas del reporte técnico
services/reporting/   # endpoints KPIs semanales
services/job_runner/  # máquina de estados job_runs (nightly)
data/pipelines/       # Prefect flow + PIPELINE_DESIGN
data/raw/             # reviews.csv, brasaland_sales.csv, exports nightly
data/forecast/        # informe + métricas train ventas
data/eval/            # informe evaluación regresión
models/               # brasaland_sales_forecast.joblib
src/                  # Hito 2 TS + sentimiento WeLoveReviews
packages/shared/      # types base + python incidents
scripts/              # analyze, nightly, train/eval ventas, seeds
tests/                # pipelines + nightly + sales forecast
docs/                 # arquitectura + telemetry + pipelines
audit/                # PNG Lighthouse (resúmenes en AUDIT/REPORT)
memory-bank/          # contexto para agentes
```

**Eliminado en limpieza 2026-08-12:** sitio estático raíz (`index.html`, `Imagenes/` PNG ~19 MB), dumps Lighthouse HTML/JSON (~10 MB), CSV duplicado, tipos “Election”, `esbuild`/demo-browser roto, SVGs create-next-app, logs/bak.

---

## 7. Flujos típicos

**Ver carta pública:** abrir `:3000`.  
**Operar inventario:** login `:3001` → Stock / Entradas / Salidas (API `:8000` + JWT).  
**Resumen incidencias:** backoffice `/incidents/resumen` → `GET /api/incidents/summary` (cache 30 s).  
**Analizar CSV:** UI en `http://localhost:8000/` o `POST /api/v1/incidents/analyze` con Bearer.

---

## 8. Informes de calidad

| Archivo | Tema |
|---------|------|
| `AUDIT.md` + `REPORT.md` + `audit/*/…png` | Lighthouse |
| `CACHING_REPORT.md` | TTL + lazy + useMemo |
| `TESTING.md` | Plan de tests |
| `docs/error-handling-audit.md` | Errores |

---

## 9. Cómo validar tras clonar

```bash
# Builds
npm run build --prefix uis/website
npm run build --prefix uis/backoffice

# API + data/ML tests (raíz con uv; API deps: services/api/requirements.txt)
uv sync
uv pip install -r services/api/requirements.txt
uv run pytest tests/pipelines tests/scripts -q
cd services/api && uv run pytest -q

# Demo dominio TS
npm run typecheck && npm run demo

# E2E website
npm run test:e2e
```

---

## 10. Memory bank (agentes)

Leer en orden: `techContext.md` → `projectbrief.md` → `progress.md`.  
Deben reflejar **este** documento; el sitio estático y el dominio elecciones ya no aplican.
