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
