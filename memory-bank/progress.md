# Progress — Brasaland Digital

## Estado (2026-10-21)
- **`main`:** PRs **#1–#52** (+ hotfixes Docker en ramas paralelas).
- **En curso:** rediseño web pública gastronómica (`cursor/website-redesign-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Rediseño website (actual)
- Next.js 16 App Router: `/`, `/carta`, `/reservas`, `/nosotros`, `/galeria`, `/eventos`, `/trabaja-con-nosotros`, `/contacto` + legales.
- Hero full-bleed + InfoStrip; carta desde `menu.json`; disclaimer 14 alérgenos UE.
- Formularios: validación + mailto; stub `lib/integrations.ts` (sin fingir envío).
- Home: rail editorial de experiencia + bloque ubicación (sin sección vacía de reseñas).
- Checks: `npm run lint` + `npm run build` OK.

## Hotfix Docker boot (`cursor/docker-boot-pythonpath-c620`)
- PYTHONPATH, entrypoint worker/flower, pandas, Redis hostname en Compose.

## Hotfix seed email (#52)
- `.env.example` → `SEED_ADMIN_EMAIL=admin@brasaland.com`.

## Hotfix Docker (#51)
- `.dockerignore` excepciones `data/` + `docs/rfp`.

## Demo delivery — gaps audit (2026-10-21)
Auditoría media de incompletos para demo pública:

**Fixeable in-repo (TinyDB/file OK):**
1. Reservas/empleo/eventos: solo mailto — no `POST` (`uis/website` forms + `lib/integrations.ts`); API sin `/api/reservations` ni `/api/careers` (`services/api/app/main.py`).
2. Contacto sin form ni mapa embebido; legales placeholder; catering `[Pendiente…]` en `data/site.ts`.
3. KB Qdrant no se indexa al boot — hace falta `POST /knowledge/reindex` (JWT) o script; sin corpus `/agent` se niega o 503 si Qdrant cae.
4. Dominio TS `ReservaMesa` en `src/` no cableado a API/web.

**Docker (ya arreglado en #51–#53):** dockerignore `data/`+`docs/rfp`, seed email TLD real, PYTHONPATH worker/flower, pandas, Redis hostname. Residual: SQLite fallback si Supabase cae; `.env` con `SEED_ADMIN_*` obligatorio para login; `services/entrypoint.sh` aún default `admin@brasaland.local` (EmailStr puede tumbar seed si falta `.env`).

**Credenciales externas (no bloquean demo con defaults):**
- `GENERATION_PROVIDER=grounded` → `/agent` sin LLM key.
- Falla si `GENERATION_PROVIDER=openai` sin `GENERATION_BASE_URL`/`GENERATION_MODEL_ID`/`GENERATION_API_KEY`.
- Opcional: `OPENAI_API_KEY` solo si `AGENT_MEMORY_LLM=1`; `RESEND_API_KEY`; portal 4Geeks embeddings; `DATABASE_URL` Supabase.

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#48 |
| NIST CSF practices | #49 |
| Pulido final UI/review | #50 |
