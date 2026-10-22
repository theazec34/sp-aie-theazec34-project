# Progress — Brasaland Digital

## Estado (2026-10-22) — candidaturas + Redis
- **Causa «Enviando…» en /trabaja-con-nosotros:** rewrite Next → `backend:8000` colgaba; website usa Route Handler `/api-backend` + timeout 15s (igual que backoffice).
- **Causa Flower/worker `Timeout connecting to redis`:** Redis con `--protected-mode yes` sin password rechaza clientes de otros contenedores → `protected-mode no` + healthcheck; worker/flower esperan `service_healthy`.
- **Website:** sin Google Fonts (stacks locales); evita reintentos a fonts.googleapis.com en Docker.
- **Hydration `bis_skin_checked`:** extensión del navegador muta el DOM; `suppressHydrationWarning` en html/body (website + backoffice). No es bug de Brasaland.
- **Favicon:** icono brasa/parrilla (terracotta sobre carbón) en website y backoffice.
- **BuildKit / disco:** `docker builder prune -af` + `scripts/docker-rebuild-clean.sh`.
- **Doc IA:** `docs/backoffice/IA-Y-API-KEYS.es.md`
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Continuidad (login Codespaces)
1. Puerto **8000 Public**; login «Usar auto-detectada» → `…-8000.app.github.dev`.
2. Proxy route-handler: `uis/backoffice/src/app/api-backend/[...path]/route.ts`.
3. IA: agente / RAG / RFP + `GENERATION_*` / `EMBEDDING_*`.

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
- Website: formularios POST vía Route Handler `uis/website/src/app/api-backend/[...path]/route.ts` → `INTERNAL_API_URL` (sin rewrite).
- Backoffice: `/web-reservations`, `/careers` (JWT).
- Mensajes honestos: solicitud **recibida**, no mesa/contrato confirmados.
- Tests: `services/api/tests/test_public_intake.py`.

## Redis / Celery (actual)
- Compose: Redis sin puertos públicos; `protected-mode no` en red interna; healthcheck `redis-cli ping`.
- Worker/Flower: `depends_on` redis healthy. Flower loopback `:5555`.
- Nota: candidaturas/reservas **no** usan Celery; el hang del form era el proxy web, no Redis.

## Rediseño website (#55)
- Rutas multi-página, hero, carta, legales, E2E.

## Hotfixes Docker (#51–#53)
- dockerignore, seed email `.com`, PYTHONPATH, Redis hostname, pandas.
