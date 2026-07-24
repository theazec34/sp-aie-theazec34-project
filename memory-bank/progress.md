# Progress Log (alineado a Brasaland.md + README)

## Completado

### A) Web Brasaland (parte visible)
- Servidor local operativo con `npm run serve` en puerto 3000.
- Navegacion corregida para secciones reales de la home (`#carta`, `#como-funciona`, `#testimonios`).
- Carta convertida a vista unica continua (sin separar por botones visibles de categoria).
- Integracion de imagenes reales desde carpeta `Imagenes` y mejoras de coherencia visual.
- Branding actualizado:
	- icono principal en logo de header/footer,
	- `rel=icon` apuntando a `Imagenes/Icono principal.png`.

### B) Documentacion interna
- Creada rama de trabajo `hito-4`.
- Creada carpeta `memory-bank/` con archivos `projectbrief.md`, `techContext.md` y `progress.md`.

## Verificacion contra fuentes oficiales

### Brasaland_Eleccion.md
La parte web implementada si va en la direccion descrita por el alumno:
- foco en restaurante,
- interes en marketing/carta,
- interes en reservas/pedidos y automatizacion.

### Brasaland.md + README
Se detecta una brecha tecnica importante:
- El dominio TypeScript exigido para hito 2 debe ser Brasaland (4 entidades de negocio).
- El codigo actual de `src/` sigue en dominio de elecciones (`Candidate`, `Vote`, `Election`).

## Estado real del proyecto hoy
- Frontend Brasaland: avanzado y funcional.
- Capa TS de hito 2 segun contexto oficial: pendiente de migracion completa al dominio Brasaland.

## Siguiente bloque de trabajo recomendado (prioridad)
1. Migrar `src/types/models.ts` a las entidades de `Brasaland.md`.
2. Reescribir `src/utils/validations.ts` con todas las reglas literales y rangos definidos.
3. Adaptar `src/demo.ts` para demostrar reportes de:
	 - encargos por estado,
	 - platos activos por categoria con resumen de precios,
	 - reservas por estado y suma de comensales confirmados,
	 - pedidos por plataforma excluyendo cancelados en sumas.
4. Alinear README si hay diferencias entre lo documentado y lo implementado.

## Actualizacion reciente
- Se creo `memory-bank/context.md` como resumen ejecutivo unificado para retomar el proyecto rapidamente.
- Se implementaron 4 skills en `skills/`:
	- `typescript-validation`
	- `web-accessibility`
	- `playwright-testing`
	- `brasaland-domain-migration` (custom)
- Se aplicaron las skills al proyecto:
	- migracion de `src/` al dominio Brasaland (tipos, validaciones y demo),
	- mejora de accesibilidad en menu movil,
	- setup de Playwright con tests e2e para home y application.
- Validacion final completada:
	- `npm run typecheck` OK,
	- `npm run demo` OK,
	- `npx playwright test` OK (4 tests passing).

## Propuesta de arquitectura backend
- Redactado `docs/architecture_proposal.md` con:
  - Patron propuesto: monolito modular + Clean Architecture + DDD por dominios.
  - Estructura de carpetas en `apps/brasaland-api/` con modulos `logistica`, `carta`, `reservas`, `domicilio`.
  - Mapa de endpoints FastAPI por dominio bajo `/api/v1/`.
  - Decisiones tecnicas iniciales (FastAPI, PostgreSQL, Pydantic, CORS para website/backoffice).
  - Riesgos: fat controllers, estructura por capas tecnicas globales, divergencia de reglas con `Brasaland.md`, acoplamiento entre dominios.

## Recuperacion y push seguro
- Se recuperaron `uis/website` y `uis/backoffice` desde commit de reflog con codigo fuente valido.
- Se endurecio `.gitignore` raiz para bloquear artefactos sensibles o pesados:
	- `**/.next/`,
	- `**/node_modules/`,
	- `**/.env*`,
	- `**/*.tsbuildinfo`.
- Se revalidaron ambas apps recuperadas:
	- `npm run lint --prefix uis/website` OK,
	- `npm run build --prefix uis/website` OK,
	- `npm run lint --prefix uis/backoffice` OK,
	- `npm run build --prefix uis/backoffice` OK.
- Objetivo de esta recuperacion: evitar nuevo rechazo GH013 por push protection (secretos en `.next` cache).

## Hito CSV — Analisis de incidencias postventa (en curso)

### Contexto del nuevo hito
- Departamento: atencion postventa de Brasaland (quejas, solicitudes, fallos operativos).
- Fuente de datos: CSV con 100 registros de prueba (`incidents-brasaland.csv`), escalable a ~1M lineas.
- Restriccion: datos sensibles (PII) — el analisis debe ejecutarse internamente, sin enviar el fichero a IA externa.
- Enfoque en dos fases:
  1. **Fase 1 (script Python):** `scripts/analyze.py` — validacion + metricas sobre el CSV de prueba.
  2. **Fase 2 (plataforma):** API en `services/api/` + interfaz en `uis/web/` (carga, resumen en pantalla, export CSV).

### Reglas de validacion (segun enunciado)
- Registro **invalido** si falta al menos un campo obligatorio (definidos en `CONTEXT-brasaland.es.md`) o si un valor no pertenece al conjunto permitido (estados/categorias).
- Los invalidos deben detectarse, contarse y **excluirse del analisis principal**, pero **nunca ignorarse en silencio**.

### Estructura objetivo del monorepo
```text
scripts/
  analyze.py
  incidents-COMPANY.csv   # incidents-brasaland.csv en este proyecto
services/
  api/
uis/
  web/
```

### Estado del repo respecto a este hito
- Rama creada: `CSV` (base: `main`).
- Carpetas `services/api/` y `uis/web/` **no existen aun** en el monorepo.
- `scripts/` solo contiene README; no hay `analyze.py` ni CSV de incidencias.
- El dominio previo del repo (`Brasaland.md`, `src/`, `uis/website`, `uis/backoffice`) cubre restaurante/operaciones, **no** incidencias postventa — este hito es un modulo nuevo.

### Bloqueo actual
- ~~Los ficheros de referencia del alumno **no estan en el entorno cloud**~~ **Resuelto** (commit `2a662c7`).

### Fase 1 completada — `scripts/analyze.py`
- Ficheros de referencia en repo: `CONTEXT-brasaland.es.md`, `incidents-brasaland.csv` (raiz) y copia en `scripts/`.
- Script implementado: `scripts/analyze.py` (stdlib `csv`, sin dependencias externas).
- Ejecucion: `python analyze.py incidents-brasaland.csv` desde `scripts/`.
- Validacion contra CONTEXT: **todos los valores numericos coinciden** (100 filas, 96 validas, 4 invalidas, desglose por categoria/estado/satisfaccion, promedio 3.46).
- Exportacion opcional a CSV (`metric`, `value`, `percentage`) al responder `y` al prompt final.

### Fase 2a completada — `services/api/`
- API FastAPI con logica compartida en `app/analyzer.py`.
- Endpoints: `GET /health`, `POST /api/v1/incidents/analyze`, `POST /api/v1/incidents/export`.
- `scripts/analyze.py` refactorizado para reutilizar el modulo compartido.
- Commit: `feat(api): añadir API FastAPI de análisis de incidencias`.

### Fase 2b completada — `uis/web/`
- Interfaz estatica HTML/CSS/JS para carga de CSV, visualizacion del resumen y descarga CSV.
- Conecta con la API configurable (`http://localhost:8000` por defecto).
- Commit: `feat(web): interfaz web de análisis de incidencias`.

### Ejecucion local completa
```bash
# Terminal 1
cd services/api && uvicorn app.main:app --reload --port 8000

# Terminal 2
cd uis/web && python3 -m http.server 8080
```

### Estado del hito
- Fases 1, 2a y 2b completadas.
- Pendiente: merge PR `CSV` → `main`.

## Exploracion AUTH/incidents centralized (2026-07-24)

Auditoria del workspace (rama local `CSV`) + contraste con `origin/main` (AUTH + proveedores ya mergeados).

### 1) Analizador CSV / API incidencias (en working tree)
- Logica: `/workspace/services/api/app/analyzer.py` (`VALID_LOCATIONS`, `VALID_CATEGORIES`, `VALID_STATUSES`, `AnalysisResult`, `analyze_*`, `build_report`).
- Schemas Pydantic reporte: `/workspace/services/api/app/schemas.py` (`AnalysisReport`, breakdowns) — **no** hay modelo `Incident`.
- Endpoints (CSV branch, sin JWT): `POST /api/v1/incidents/analyze`, `POST /api/v1/incidents/export`, `GET /health`.
- CLI: `/workspace/scripts/analyze.py` reutiliza el analyzer via `sys.path` → `services/api`.
- UI estatica: `/workspace/uis/web/` llama a `/api/v1/incidents/{analyze,export}`.

### 2) Modelo Incident
- **No existe** entidad CRUD `Incident` / `IncidentRepository` / TinyDB `incidents` en ninguna rama revisada (`CSV`, `origin/main`).
- Filas CSV se tratan como `dict[str, str]`; unico “modelo” de dominio analitico es `AnalysisResult` + `AnalysisReport`.

### 3) CSV historico
- `/workspace/incidents-brasaland.csv` y copia identica `/workspace/scripts/incidents-brasaland.csv` (100 filas + header).
- Columnas: `incident_id,date,location_id,category,description,status,customer_id,satisfaction_score,reporter_id`.

### 4) CONTEXT — categorias / sedes
- Incidencias: `/workspace/CONTEXT-brasaland.es.md`
  - Sedes: `COL-01`…`COL-10`, `FLA-01`…`FLA-04` (14).
  - Categorias: `CUSTOMER_COMPLAINT`, `EQUIPMENT`, `SUPPLY`, `FOOD_QUALITY`, `STAFF`.
  - Estados: `OPEN`, `CLOSED`, `DISCARDED`.
- Proveedores (en `origin/main`, no en working tree CSV): `09-lightweight-storage/CONTEXT-brasaland.md` — categorias compra distintas (`carne`, `verduras_y_hortalizas`, …).
- Backoffice hito2: `/workspace/uis/backoffice/context hito2.md` (MenuCategory Meat/Side/…; Location ids tipo `LOC-MEDELLIN-01` — distinto del CSV).

### 5) Backoffice
- **Working tree `CSV`:** shell Next.js minimo — hash-nav en `page.tsx`, sin auth, sin `/proveedores`.
- **`origin/main`:** `AppNav` + `RequireAuth` + `lib/auth.ts` / `lib/api.ts` (JWT localStorage, Bearer, 401→login); paginas `/login`, `/register`, `/proveedores`, `/account/profile`, forgot/reset/change-password. **Sin pagina Incidencias** aun.

### 6) `packages/shared`
- Existe: `packages/shared/package.json` (`@repo/shared-types`) + `packages/shared/types/index.ts`.
- Contenido: tipos elecciones (`Candidate`, `Vote`, `Election`) — **sin** tipos Incident/Supplier/User.

### 7) TinyDB (solo en `origin/main` / ramas auth-proveedores; **ausente en working tree CSV**)
- Suppliers: `services/api/data/suppliers.json`, table `suppliers` — CRUD + seed (`seed.py`).
- Users/Profiles/reset: `services/api/data/auth.json`, tables `users`, `profiles`, `password_reset_tokens` — `seed_auth.py`.
- Patron: repo class → `TinyDB` + `Query` + `doc_id` como `id` + `close()` en finally de routers.

### 8) Rutas API
- **`/api/incidents` no existe** (ninguna rama).
- Solo: `/api/v1/incidents/analyze` y `/api/v1/incidents/export`.
- En `origin/main` esos endpoints exigen `Depends(get_current_user)`.

### Gap para milestone AUTH/incidents centralized
- Falta persistencia TinyDB de incidencias, router CRUD `/api/.../incidents`, modelo Pydantic `Incident`, pagina backoffice, y posible unificacion bajo auth ya existente en `origin/main`.
- Working tree `CSV` esta **detras** de `origin/main` (falta suppliers + AUTH-01/02/03).
