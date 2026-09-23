# Project Brief — Brasaland Digital

## Negocio
Restaurante Brasaland: sala, carta/marketing, logística/proveedores, domicilio e incidencias postventa.

## Entidades TS (`Brasaland.md` → `src/`)
- `EncargoProveedor`
- `PlatoCarta`
- `ReservaMesa`
- `PedidoDomicilio`

## Producto en main
Plataforma digital con:
1. Web pública Next (`uis/website`)
2. Backoffice ops Next (`uis/backoffice`) — telemetría, reporting, knowledge
3. API FastAPI (`services/api`) — auth JWT, proveedores, incidencias, inventario, telemetry, reporting, knowledge, tasks, agent
4. Docker Compose + informes de performance/caching
5. Pipeline Prefect + nightly export (`job_runs`)
6. ML: sentimiento WeLoveReviews + forecast/eval de ventas
7. RAG: base de conocimiento Qdrant (`brasaland_knowledge`) + `/knowledge`
8. Celery/Redis (DEV-55): analyze async + Flower
9. LangGraph agent (Part 1): grafo explícito sobre RAG + `/agent/query`

## Fuentes de verdad
- Mapa operativo: **`PROJECT.md`**
- Negocio restaurante: `Brasaland.md`
- Incidencias CSV / centralizadas / inventario: CONTEXT*.md correspondientes
- RAG: `docs/rag/CONTEXT-brasaland.es.md`

## Fuera de alcance en main
- Talent Pipeline Tracker (`hito-3` / rama `3.5`) — no mergeado
- Brasaland Agent experimental histórico — sustituido por `services/agent` LangGraph
