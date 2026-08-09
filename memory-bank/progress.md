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
- Rama `CSV` creada y **mergeada a `main`** vía PR #5.
- En `main` existen: `scripts/analyze.py`, `scripts/incidents-brasaland.csv`, `services/api/`, `uis/web/`, `CONTEXT-brasaland.es.md`.

### Auditoría main (2026-07-15)
- **Hito CSV:** completo en `main` (script + API + web). No falta nada de ese trabajo.
- **Hitos ya mergeados previamente:** Hito 4, recuperación website/backoffice, propuesta arquitectura, skills/migración dominio Brasaland.
- **Ramas remotas con commits no mergeados a main** (trabajo distinto, no del CSV):
  - `hito-3-talent-pipeline-tracker` / `3.5` → Talent Pipeline Tracker (`apps/talent-pipeline-tracker/`)
  - `brasaland_agent` → agente con memoria persistente
- No hay PRs abiertas.

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
- **PR #5 mergeado a `main`** (2026-07-13).

### Fix Codespaces (failed to fetch)
- En Codespaces `localhost:8000` no funciona desde el navegador.
- Rama `cursor/codespaces-cors-api-c620`: CORS abierto + auto-detección de URL del puerto 8000 en la UI.

## Hito Directorio de Proveedores (rama `proveedores`)

### Alcance
- CONTEXT: `09-lightweight-storage/CONTEXT-brasaland.md`
- Misma API FastAPI (`services/api`) + TinyDB + backoffice (`uis/backoffice/proveedores`)

### Commits
1. `feat(proveedores): modelo Pydantic Supplier según CONTEXT`
2. `feat(proveedores): seeder TinyDB con 15 proveedores del CONTEXT`
3. `feat(proveedores): endpoints FastAPI /suppliers`
4. `feat(proveedores): página backoffice del directorio`

### Cómo arrancar
```bash
cd services/api && python seed.py && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd uis/backoffice && npm run dev
# Abrir http://localhost:3000/proveedores
```

### Nota
- El PR a `main` lo abre el alumno desde la rama `proveedores`.

## Hito Users & Profile (en curso)
- Rama de trabajo: `users&profile` (creada desde `main` actualizado).
- AUTH-01 implementado en `services/api`:
  1. Modelos User/Profile + TinyDB (`auth.json`)
  2. JWT + bcrypt + `get_current_user`
  3. Rutas `/auth`, `/users`, `/profiles` + `seed_auth.py`
  4. Rutas protegidas: todo `/suppliers` + incidencias analyze/export
- `.env` gitignored; usar `.env.example`
- Tooling: `uv` + `.venv` en raíz del monorepo
- PR a `main`: lo abre el alumno desde GitHub

## Hito AUTH-02 Frontend (rama `Funcionamiento_Total`)
- `/login` y `/register` en backoffice (token en localStorage)
- `/account/profile` con GET /auth/me y PUT /profiles/me
- RequireAuth en dashboard, proveedores y perfil
- apiFetch + logout + 401 → login; uis/web con login JWT
- Website público (`uis/website`) sin auth
- Fix UX `Failed to fetch`: campo editable URL API en login/register + mensaje de diagnóstico (puerto 8000 Public / Codespaces)
- Nota: el admin sembrado (`seed_auth.py`) debe usar **Iniciar sesión**, no registrarse otra vez
- PR #11 y #12 mergeados a `main`

## Hito AUTH-03 Recuperación y cambio de contraseña (rama `Recuperar_contraseña`)
- Backend:
  - `POST /auth/forgot-password` (siempre 200, anti-enumeración)
  - `POST /auth/reset-password` (JWT corto + jti single-use en TinyDB)
  - `POST /auth/change-password` (Bearer + verifica contraseña actual)
- Email: **Resend** (`RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `FRONTEND_URL`); HTML + rate-limit; fallback consola sin clave
- Frontend backoffice:
  - `/forgot-password`, `/reset-password?token=...`, `/account/change-password`
  - Enlace «¿Olvidaste tu contraseña?» en `/login`
- PR a `main`: lo abre el alumno

## Hito Gestor de Incidencias Centralizado (rama `incidents-centralized`)
- CONTEXT: `CONTEXT-incidents-centralized.es.md`
- Modelo TinyDB + seed desde `incidents-brasaland.csv` (96 válidos; conteos CONTEXT OK)
- Helpers compartidos: `packages/shared/python/brasaland_incidents/`
- API pública: `POST/GET /api/incidents`, `GET /summary`, `GET/{id}`, `PATCH /{id}/status`
- Errores 400 por campo / 500 genérico (sin stack trace)
- Backoffice: `/incidents/nueva`, `/incidents`, `/incidents/resumen`
- Analizador legacy `/api/v1/incidents/analyze|export` intacto
- PR mergeado a `main`

## Hito Error-handling audit (rama `error-handling-audit`)
- Informe: `docs/error-handling-audit.md`
- Backend: 500 con log interno, UTF-8 CSV → 400, sin filtrar paths/JWT
- Scripts: I/O defensivo + exit codes
- Backoffice: loading/error/CTA + `lib/errors.ts` + `error.tsx`
- `uis/web` + website: mensajes legibles; formulario demo honesto
- Sin nuevas features (solo gestión de errores)
- PR mergeado a `main`

## Hito AUTH-088 Testing (rama `limit_testing`)
- `TESTING.md` en raíz (plan + cómo ejecutar + resultados)
- pytest en `services/api/tests/`: register, login, me, profiles, forgot/reset/change-password
- Extras bulletproof: anti-enumeración, token malformado/reusado, usuario inactivo
- Ampliación: suppliers + incidents; Jest en `uis/backoffice` (auth/errors + incidents utils)
- `uv run pytest` → 40 passed; Jest → 10 passed; cov auth~82%
- PR a `main`: lo abre el alumno

## Hito Inventario ORM backend (rama `inventory-orm`) — en curso
- CONTEXT: `05-backend-inventory-orm/CONTEXT-brasaland.es.md`
- Integrado en `services/api/app/` (no layout literal `services/main.py` del enunciado).
- Dual DB: TinyDB (auth/users/…) + SQLModel (`DATABASE_URL` Supabase o SQLite local).
- Modelos: `Ingredient`, `IngredientEntry`, `IngredientExit` — sin `current_stock` persistido.
- Rutas JWT bajo `/inventory/products` y `/inventory/orders/*`.
- **`user_uuid` = id numérico TinyDB como string** (ej. `"1"`), no UUID Supabase.
- Seed: `seed_inventory.py` (≥6 ingredientes, ≥4 entradas, ≥3 salidas con 1 waste).
- Frontend fotos / UI inventario: pendiente (hito posterior).
- Smoke local: stock BRS-BEEF-001 = 68.0; outbound excesivo → 400 mensaje CONTEXT; pytest auth 40 OK.
