# Brasaland Digital

Monorepo del restaurante **Brasaland**: web corporativa, backoffice operativo y API FastAPI.

> Guía completa de arquitectura, hitos, puertos y operación: **[PROJECT.md](./PROJECT.md)**  
> Docker: **[DOCKER.md](./DOCKER.md)**

## Arranque rápido (local)

```bash
# API (puerto 8000)
cd services/api && uv sync && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Website (puerto 3000)
cd uis/website && npm install && npm run dev

# Backoffice (puerto 3001)
cd uis/backoffice && npm install && npm run dev

# Redis + Celery worker (DEV-55) — proceso independiente
redis-server --daemonize yes --maxmemory-policy noeviction
cd services && PYTHONPATH=. uv run celery -A celery_app.celery worker --loglevel=INFO
# Flower (opcional): PYTHONPATH=. uv run celery -A celery_app.celery flower --port=5555
```

O con Docker desde la raíz:

```bash
cp .env.example .env
docker compose up --build
```

| Servicio | URL |
|----------|-----|
| Website | http://localhost:3000 |
| Backoffice | http://localhost:3001 |
| API + docs | http://localhost:8000/docs |
| Flower (Celery) | http://localhost:5555 |

## Qué hay en este repo

| Ruta | Rol |
|------|-----|
| `uis/website` | Sitio público Next.js (carta, galería, formulario) |
| `uis/backoffice` | Panel ops (+ `/telemetry`, `/reporting`, `/knowledge`) |
| `uis/web` | UI CSV en `:8000/` (analyze async → poll `/tasks/{id}`) |
| `services/api` | FastAPI monolito modular |
| `services/celery_app.py` + `tasks/` | Celery worker (Redis broker) |
| `services/telemetry` / `reporting` / `job_runner` / `knowledge` | Módulos de dominio |
| `data/pipelines` | Prefect + RAG query pipeline |
| `docs/company-knowledge-base` | Corpus RAG |
| `scripts/` | analyze, nightly, train/eval ventas, eval RAG |
| `src/` | Dominio TS + sentimiento WeLoveReviews |
| `models/` + `data/forecast/` + `data/eval/` | Artefactos ML |

## Comandos útiles (raíz)

| Comando | Descripción |
|---------|-------------|
| `npm run typecheck` / `npm run demo` | Capa TS Brasaland en `src/` |
| `npm run test:e2e` | Playwright → website `:3000` |
| `npm run test:api` | pytest FastAPI |
| `uv run pytest tests/pipelines tests/scripts -q` | Pipeline, forecast, nightly, RAG |

## Contexto de negocio

- [Brasaland.md](./Brasaland.md) — entidades y reglas del restaurante  
- [CONTEXT-brasaland.es.md](./CONTEXT-brasaland.es.md) — predicción de ventas  
- [docs/rag/CONTEXT-brasaland.es.md](./docs/rag/CONTEXT-brasaland.es.md) — RAG knowledge base  
- [CONTEXT-incidents-centralized.es.md](./CONTEXT-incidents-centralized.es.md) — incidencias  
- [docs/telemetry/](./docs/telemetry/) / [docs/pipelines/](./docs/pipelines/) / [docs/rag/](./docs/rag/)  

## Estado Git

Producto en **`main`** (PRs #1–#21, #23–#35): web, backoffice, API, Docker, telemetría, pipeline, nightly, sentimiento, forecast/eval, RAG. Hito Celery/Redis (DEV-55) en PR `async-tasks`. Detalle: [PROJECT.md](./PROJECT.md).
