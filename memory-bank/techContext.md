# Technical Context (concreto y actualizado)

## Runtime y scripts reales
- Node.js >= 18 (segun `package.json`).
- Scripts disponibles:
	- `npm run typecheck` -> `tsc --noEmit`
	- `npm run build` -> `tsc`
	- `npm run demo` -> build + `node dist/demo.js`
	- `npm run build:web` -> bundle browser con `esbuild`
	- `npm run serve` -> `http-server` en puerto 3000

## Estructura relevante actual
- Web restaurante:
	- `index.html`
	- `application.html`
	- `validation.js`
	- `menu.json`
	- `Imagenes/*`
- Capa TypeScript existente:
	- `src/types/models.ts`
	- `src/utils/collections.ts`
	- `src/utils/search.ts`
	- `src/utils/transformations.ts`
	- `src/utils/validations.ts`
	- `src/demo.ts`

## Requisito de negocio/academico (fuente: Brasaland.md)
El modelo de dominio esperado en TypeScript debe basarse en 4 entidades:
- `EncargoProveedor`
- `PlatoCarta`
- `ReservaMesa`
- `PedidoDomicilio`

Con reglas estrictas de validacion (ISO, rangos, literales permitidos) y reportes de agregacion por estado/categoria/plataforma.

## Hallazgo importante de coherencia
Actualmente `src/` no implementa aun ese dominio Brasaland:
- `src/types/models.ts` reexporta tipos de elecciones desde `packages/shared/types`.
- `src/utils/validations.ts` valida `Candidate`, `Vote`, `Election`.
- `src/demo.ts` ejecuta demo de "sistema de elecciones".

Conclusión tecnica: la parte web refleja Brasaland, pero la parte TypeScript de hito 2 sigue en dominio distinto y necesita migracion para quedar acorde con `Brasaland.md` y README.

## Frontend realizado sobre Brasaland
- Favicon y logo usan `Imagenes/Icono principal.png`.
- Carta en vista unica (sin tabs visibles).
- Carga de menu desde `menu.json` con fallback inline.
- Integracion de imagenes de platos mediante mapeo en JS.

## Estado de rama
- Rama activa de trabajo: `cursor/caching-optimisation-c620` (caching TTL + lazy/memo).
- `main` incluye performance audit Lighthouse + Docker + inventario.

## Caching
- `services/api/app/cache.py` — `TtlCache` in-process (incidents + suppliers).
- Timing middleware en `app/main.py` (`api.timing`, `X-Response-Time-Ms`).
- Seed de carga: `services/api/seed_load.py`.
- Informe: `CACHING_REPORT.md`.
- Frontend: `next/dynamic` en website (Gallery + Form) y backoffice (`SupplierCreateForm`); `useMemo` en inventory products.

## Inventario (dual DB)
- Motor SQL: `services/api/app/database.py` (`get_db`, `init_db`).
- Dominio: `services/api/app/inventory/` (models, schemas, stock, router).
- `DATABASE_URL` en `.env` → Postgres/Supabase; vacío → SQLite `services/api/data/inventory.db`.
- Auth sigue en TinyDB; no hay tabla User en SQL.

## Nuevo hito CSV (Python + API + web)
- Script objetivo: `scripts/analyze.py` (Fase 1).
- Datos de prueba: `scripts/incidents-brasaland.csv` (100 registros).
- Backend objetivo: `services/api/` (FastAPI o similar, pendiente de definir al integrar).
- UI objetivo: `uis/web/` (carga CSV, resumen, exportacion).
- Contexto de negocio especifico: `CONTEXT-brasaland.es.md` (incidencias postventa; distinto de `Brasaland.md`).
