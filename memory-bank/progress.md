# Progress — Brasaland Digital

## Estado (2026-10-21)
- **`main`:** PRs **#1–#62** (+ intake/hotfixes en ramas).
- **En curso:** backoffice `failed to fetch` → proxy `/api-backend` (`cursor/backoffice-api-proxy-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Backoffice API proxy (actual)
- Mismo patrón que website: browser → `/api-backend/*` → rewrite `INTERNAL_API_URL`.
- Evita `Failed to fetch` cuando `localhost:8000` no es alcanzable desde el navegador (Codespaces/Docker).
- WebSocket del agente sigue en origen directo `:8000` (rewrite Next no hace upgrade WS).
- Guía módulos + muestras: `docs/backoffice/GUIA-MODULOS.es.md`, `data/samples/backoffice/`.

## Pulido páginas web (actual)
- Sin etiquetas «provisional»; banners con foto; Eventos (flamenco/vivo); Empleo (sala/brasas).
- Contacto con Google Maps embed; textos legales con razón social / NIF.
- Tipografía y CTAs más destacados; build/lint OK.
- Galería: «Corte a la brasa» → `Corte carne.jpg` (foto antigua); «Entraña argentina» → `entrana-chimichurri.jpg` (foto nueva distinta).
- Carta: fotos generadas únicas por plato (tira asado, picanha, ribeye, croquetas, patacón, empanadas, pulpo, arroz negro, arroz pollo, paella, tres leches, churros, alfajores, flan) — sin reutilizar placeholders.
- Home: banner Experiencia con fondo espectáculo en vivo; hero/ubicación HQ; Operaciones = descarga de mercancía (ya no duplica Sala).

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
