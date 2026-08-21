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
