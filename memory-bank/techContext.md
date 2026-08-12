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

## Rama
- Trabajo de limpieza/docs: `cursor/project-cleanup-docs-c620`
- Producto estable: **`main`**
