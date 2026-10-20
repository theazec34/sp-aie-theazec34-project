# Revisión final — Brasaland Digital

**Fecha:** 2026-10-20 · Tras merge PRs **#1–#49**

## Cómo ver el producto

```bash
cp .env.example .env
# Ajusta SECRET_KEY y SEED_ADMIN_* si hace falta
docker compose up --build
```

| Superficie | URL |
|------------|-----|
| Web pública (carta / reserva) | http://localhost:3000 |
| Backoffice (ops + IA) | http://localhost:3001 |
| API + docs | http://localhost:8000/docs |

Login backoffice: el seed crea admin vía `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` (ver `.env.example`).

Sin Docker: website `uis/website` `:3000`, backoffice `uis/backoffice` `:3001`, API `cd services/api && uv run uvicorn app.main:app --reload --port 8000`.

---

## Qué incluye el monorepo (mapa corto)

| Área | Piezas |
|------|--------|
| Público | Carta, galería, formulario — `uis/website` |
| Ops | Proveedores, incidencias, inventario, telemetría, reporting — `uis/backoffice` |
| Auth | JWT, registro, reset password |
| IA | Agente LangGraph + guardrails + memoria + MCP; RAG Qdrant; chat WS; SSE RFP |
| RFP | Intake → generación → HITL → documento final (€) |
| Data/ML | Pipeline Prefect, nightly export, forecast ventas, sentimiento |
| Seguridad | OWASP #48, NIST CSF #49, hardening Compose |

Detalle histórico: `PROJECT.md`.

---

## Hallazgos de esta pasada (y estado)

### Críticos corregidos aquí

1. **`skipAuth` en crear/cambiar incidencias** tras exigir JWT en API → 401 en UI. Fixed en `incidents/page.tsx` y `nueva/page.tsx`.
2. Login redirigía a `/proveedores` en vez del panel → ahora `/`.

### Visual / marca

- Backoffice era **slate/cyan SaaS**; se alineó a **carbón + brasa** (`#1a1008` / `#c8380a`) compartido con la web.
- Hero web: marca **Brasaland** a nivel hero, full-bleed atmosférico, sin tarjeta “Next.js”.
- Copy ES con tildes en hero, formulario, menú, agente y RFP.
- Módulos del panel: CTAs `.bo-module-link` (sin estilos cyan inline).

### Incongruencias conocidas (no bloqueantes)

| Tema | Nota | Mitigación sugerida |
|------|------|---------------------|
| Nav backoffice larga (15 enlaces) | Sin agrupación por dominio | Agrupar en “Ops / Inventario / IA / Cuenta” en un hito UX |
| Rate limit in-memory | Un worker | Redis (gap NIST) |
| Flower / Redis | Solo red interna / loopback | OK en compose endurecido |
| `PROJECT.md` mapa puertos | Parcialmente desactualizado vs compose | Actualizado en este PR de forma ligera |

### Optimización

- Website ya difería formulario y galería (`dynamic`) — se mantiene.
- Hero ahora es texto LCP (sin imagen pesada en primer viewport); atmósfera CSS.
- Evitar reintroducir `skipAuth` en rutas JWT.

---

## Checklist visual Brasaland

- [x] Web: marca dominante en primer viewport  
- [x] Backoffice: acento brasa, no cian  
- [x] Español de producto con tildes en superficies tocadas  
- [x] Bug auth incidencias  
- [x] Login → panel  
