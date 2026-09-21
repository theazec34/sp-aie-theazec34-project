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

## Qué hay en este repo

| Ruta | Rol |
|------|-----|
| `uis/website` | Sitio público Next.js (carta, galería, formulario) |
| `uis/backoffice` | Panel ops (auth, proveedores, incidencias, inventario, `/telemetry`, `/reporting`) |
| `uis/web` | UI ligera del analizador CSV (servida por la API en `/`) |
| `services/api` | FastAPI: JWT, proveedores, incidencias, inventario, telemetry, reporting |
| `services/telemetry` / `reporting` / `job_runner` | Análisis reporte, KPIs, orquestación nightly |
| `data/pipelines` | Prefect flow de performance semanal |
| `scripts/` | `analyze.py`, `nightly_export.py`, train/eval ventas, seeds |
| `src/` | Dominio TS Brasaland + pipeline sentimiento WeLoveReviews |
| `models/` + `data/forecast/` + `data/eval/` | Artefactos ML de ventas |
| `audit/` | Screenshots Lighthouse before/after |
| `CACHING_REPORT.md` / `AUDIT.md` / `REPORT.md` | Informes de rendimiento |

## Comandos útiles (raíz)

| Comando | Descripción |
|---------|-------------|
| `npm run typecheck` / `npm run demo` | Capa TS Brasaland en `src/` |
| `npm run test:e2e` | Playwright → website `:3000` |
| `npm run test:api` | pytest FastAPI |
| `uv run pytest tests/pipelines tests/scripts -q` | Pipeline, forecast split, nightly |

## Contexto de negocio

- [Brasaland.md](./Brasaland.md) — entidades y reglas del restaurante  
- [CONTEXT-brasaland.es.md](./CONTEXT-brasaland.es.md) — predicción de ventas (CSV + métricas)  
- [CONTEXT-incidents-centralized.es.md](./CONTEXT-incidents-centralized.es.md) — gestor centralizado de incidencias  
- [05-backend-inventory-orm/CONTEXT-brasaland.es.md](./05-backend-inventory-orm/CONTEXT-brasaland.es.md) — inventario ORM  
- [docs/telemetry/](./docs/telemetry/) / [docs/pipelines/](./docs/pipelines/) — telemetría y pipeline de negocio  

## Estado Git

Producto en **`main`** (PRs #1–#21 y #23–#33): web, backoffice, API, Docker, performance, caching, telemetría, pipeline, nightly, sentimiento y forecast/eval de ventas. Detalle: [PROJECT.md](./PROJECT.md).
