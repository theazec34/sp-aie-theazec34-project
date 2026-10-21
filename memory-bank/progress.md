# Progress — Brasaland Digital

## Estado (2026-10-21) — cierre de día
- **`main`:** PRs **#1–#67** (website polish, proxy backoffice, login hang, URL input).
- **Pendiente mañana:** acceso login en Codespaces (proxy) + explicación IA / `GENERATION_*` API keys.
- **Doc continuidad IA:** `docs/backoffice/IA-Y-API-KEYS.es.md`
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Continuidad mañana
1. Codespaces: puerto 8000 **Public**; login con auto-detect (`…-8000.app.github.dev`) si `/api-backend` timeout.
2. Verificar proxy route-handler `uis/backoffice/src/app/api-backend/[...path]/route.ts`.
3. Repasar IA: agente, RAG, RFP + variables `GENERATION_*` / `EMBEDDING_*` (ver doc arriba).

## Backoffice API proxy (actual)
- Mismo patrón que website: browser → `/api-backend/*` → rewrite `INTERNAL_API_URL`.
- Evita `Failed to fetch` cuando `localhost:8000` no es alcanzable desde el navegador (Codespaces/Docker).
- WebSocket del agente sigue en origen directo `:8000` (rewrite Next no hace upgrade WS).
- Guía módulos + muestras: `docs/backoffice/GUIA-MODULOS.es.md`, `data/samples/backoffice/`.
- Menú lateral alineado con el orden del panel (Reservas → Candidaturas → …).
- Compose: fallback `SECRET_KEY` + seed `seed_public_intake.py` (demo reserva/candidatura). Sin `SECRET_KEY` el login devolvía HTTP 500.
- Login colgado «Entrando…»: healthcheck backend, interfaces espera healthy, timeout 12s en login, sin Google Fonts en backoffice (fallaban en Docker), seed_inventory en background.

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
