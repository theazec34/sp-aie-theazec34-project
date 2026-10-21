# Progress — Brasaland Digital

## Estado (2026-10-21)
- **`main`:** PRs **#1–#55** (+ intake/hotfixes en ramas).
- **En curso:** pulido páginas web (eventos/empleo/contacto/legales) `cursor/website-pages-polish-c620`.
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Pulido páginas web (actual)
- Sin etiquetas «provisional»; banners con foto; Eventos (flamenco/vivo); Empleo (sala/brasas).
- Contacto con Google Maps embed; textos legales con razón social / NIF.
- Tipografía y CTAs más destacados; build/lint OK.

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
