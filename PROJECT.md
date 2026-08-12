# PROJECT — Mapa completo Brasaland Digital

Documento canónico del monorepo (actualizado 2026-08-12). Sustituye lecturas antiguas de README/memory-bank que hablaban del sitio estático o del dominio de “elecciones”.

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
  └─ :8000  services/api    FastAPI
              ├─ /docs, /health, /auth, /users, /profiles
              ├─ /suppliers, /api/incidents*, /inventory/*
              └─ /  → uis/web (analizador CSV estático)
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

Todos estos PRs están **MERGED** en `main` (sin PRs abiertos a 2026-08-12):

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

### Ramas remotas **no** mergeadas (fuera del producto principal)

| Rama | Contenido | Por qué no está en main |
|------|-----------|-------------------------|
| `hito-3-talent-pipeline-tracker` / `3.5` | App Next “Talent Pipeline” en `apps/` | Hito académico paralelo, no es ops Brasaland |
| `brasaland_agent` | Agente TS + memoria | Experimento; no forma parte del runtime Docker |
| Varias `cursor/*` solo docs | Notas en `progress.md` | Ya absorbidas o redundantes |

Si quieres fusionar Talent Pipeline o el Agent, hacerlo en PRs dedicados (añaden mucho código ajeno al stack actual).

---

## 5. Puntos fuertes

1. **Monorepo operable de punta a punta** — tres superficies + API real, no mocks.  
2. **Auth completa** — register/login/JWT, perfil, forgot/reset/change password.  
3. **Dominios de negocio claros** — proveedores, incidencias (CSV + CRUD), inventario con stock calculado.  
4. **Dual DB pragmática** — TinyDB para ops ligeras; SQLModel para inventario (Supabase o SQLite).  
5. **Rendimiento documentado** — Lighthouse before/after + cache TTL con invalidación y informe.  
6. **Docker one-shot** — `compose up` con fallback si Supabase no responde.  
7. **Tests** — pytest API, Jest backoffice, Playwright website.  
8. **Dominio TS Brasaland en `src/`** — EncargoProveedor / PlatoCarta / ReservaMesa / PedidoDomicilio + reportes.

---

## 6. Mapa de carpetas (qué importa)

```text
uis/website/          # CANÓNICO sitio público
uis/backoffice/       # CANÓNICO panel ops
uis/web/              # UI CSV servida por API
services/api/         # CANÓNICO backend
src/                  # Hito 2 TypeScript Brasaland
packages/shared/      # types base + python incidents
scripts/              # analyze + seeds
audit/                # solo PNG Lighthouse (resúmenes en AUDIT/REPORT)
docs/                 # arquitectura
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
