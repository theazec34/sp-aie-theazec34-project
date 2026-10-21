# Progress — Brasaland Digital

## Estado (2026-10-21)
- **`main`:** PRs **#1–#52** (seed email #52 mergeado).
- **Hotfix en curso:** boot Docker — `PYTHONPATH` + entrypoint worker/flower (`cursor/docker-boot-pythonpath-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Hotfix Docker boot (actual)
- Causa 1: `entrypoint.sh` hacía `PYTHONPATH=.` → `ModuleNotFoundError: data.pipelines`.
- Causa 2: el entrypoint ignoraba el `command` de Compose → worker/flower arrancaban uvicorn.
- Causa 3: falta `pandas` en `services/api/requirements.txt` (telemetry).
- Causa 4: `.env` con `REDIS_URL=127.0.0.1` rompe worker/flower en Compose.
- Fix: PYTHONPATH, `exec "$@"`, pandas, Redis/Qdrant hostnames fijos en compose, migrate `.local`.
- Demo: `docker compose up --build` tras pull de esta rama.

## Hotfix seed email (#52)
- `.env.example` → `SEED_ADMIN_EMAIL=admin@brasaland.com`.
- **`main`:** PRs **#1–#52** (+ hotfixes Docker en ramas paralelas).
- **En curso:** rediseño web pública gastronómica (`cursor/website-redesign-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Rediseño website (actual)
- Next.js 16 App Router: `/`, `/carta`, `/reservas`, `/nosotros`, `/galeria`, `/eventos`, `/trabaja-con-nosotros`, `/contacto` + legales.
- Hero full-bleed + InfoStrip; carta desde `menu.json` (sin inventar categorías vacías).
- Formularios reservas/empleo: validación + mailto; **no** fingen confirmación/envío al servidor.
- Footer profesional; leyenda 14 alérgenos UE; E2E actualizados.
- Checks: `npm run lint` + `npm run build` en `uis/website` OK.

## Hotfix Docker boot (`cursor/docker-boot-pythonpath-c620`)
- PYTHONPATH, entrypoint worker/flower, pandas, Redis hostname en Compose.

## Hotfix seed email (#52)
- `.env.example` → `SEED_ADMIN_EMAIL=admin@brasaland.com`.

## Hotfix Docker (#51)
- `.dockerignore` excepciones `data/` + `docs/rfp`.

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#48 |
| NIST CSF practices | #49 |
| Pulido final UI/review | #50 |
