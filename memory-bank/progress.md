# Progress — Brasaland Digital

## Estado (2026-10-21)
- **`main`:** PRs **#1–#55** (rediseño web #55 mergeado).
- **En curso:** conexiones públicas reservas/empleo (`cursor/public-intake-api-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Public intake (actual)
- API: `POST/GET /reservations`, `POST/GET /careers` (TinyDB `public_intake.json`).
- Website: formularios POST vía `/api-backend` (rewrite → `INTERNAL_API_URL`).
- Backoffice: `/web-reservations`, `/careers` (JWT).
- Mensajes honestos: solicitud **recibida**, no mesa/contrato confirmados.
- Tests: `services/api/tests/test_public_intake.py`.

## Rediseño website (#55)
- Rutas multi-página, hero, carta, legales, E2E.

## Hotfixes Docker (#51–#53)
- dockerignore, seed email `.com`, PYTHONPATH, Redis hostname, pandas.
