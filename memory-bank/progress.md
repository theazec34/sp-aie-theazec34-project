# Progress — Brasaland Digital

## Estado (2026-10-23) — Agente respeta Local/sede + indicador en vivo
- Bug: al cambiar el desplegable «Local / sede», la sesión WS reutilizaba
  `session_id` y **no actualizaba** `location_id` (quedaba `miami_doral`).
- Fix backend: `ChatSessionStore.get_or_create` siempre pisa `location_id`.
- Fix UI: al cambiar sede → `freshSession` (nuevo chat) + muestra «Sede
  activa»; badge verde «En vivo (WebSocket)» = canal WS abierto.
- Tests: `test_agent_chat_ws` (store + reconnect con sede nueva).

## Estado previo — Agente inprocess sin fastmcp
- Contenedor sin DNS a PyPI → no se puede instalar fastmcp.
- Fix: `mcps/.../inprocess_tools.py` (handlers vía backend.py); el agente
  con `MCP_INPROCESS=1` ya no importa FastMCP.

## Estado previo — Agente: fastmcp en imagen Docker
- Deps MCP en `services/api/requirements.txt` (para rebuild con red).

## Estado previo — Agente proveedores: montar ./mcps
- Volume `./mcps:/app/mcps` en backend/worker.

## Estado previo — BrasAI reindex async (HTTP 504)
- Reindex sync con embeddings 4Geeks superaba el proxy → **HTTP 504**.
- Fix: `POST /knowledge/reindex` en background + `GET …/status`; UI hace poll;
  `embed_many` por lotes; volume `services/knowledge` montado en compose.

## Estado previo — Qdrant local lock BrasAI
- Cliente Qdrant cacheado; `QDRANT_FORCE_LOCAL=0` con Compose.

## Estado previo — BrasAI manuales + agente front_ops
- Manuales ampliados + nuevos: `service-hours`, `customer-experience`.
- Agente: `query_front_ops`; suppliers sin fallback vacío; `location_id`.
- MCP rehidrata suppliers; scope `intake:read`.

## Estado previo — LLM vía host proxy (Codespaces)
- Tras `extra_hosts`, DNS OK pero `curl :443` desde backend → **timeout**
  (host sí 200). Bridge sin egress TCP.
- Fix: servicio `llm-proxy` (nginx `network_mode: host` :18080) +
  `scripts/codespace-enable-llm-proxy.sh` apunta BASE_URL a
  `http://host.docker.internal:18080/v1`.

## Estado previo — DNS egress backend → llm.4geeks.ai
- `extra_hosts` + DNS públicos; `scripts/codespace-fix-llm-dns.sh`.

## Estado previo — sinónimos fidelización + .env (no export)
- `export` en shell **no** basta: Docker Compose lee el fichero `.env`. Tras cambiar LLM, verificar `docker compose exec backend printenv EMBEDDING_PROVIDER`.
- Keyword RAG: sinónimos (`fidelización`→loyalty/puntos/oro) para no devolver supplier-ordering.

## Estado previo — seed demo multi-sede + RAG hash keyword-first
- `seed_demo_ops.py` multi-sede; keyword-first con hash.

## Estado previo — BrasAI razona con LLM si hay API key
- LLM auto si `GENERATION_*` + key; `RAG_MIN_SCORE` bajo con hash; offscope menú.

## Estado previo — BrasAI keyword + Agente HTTP fallback
- Keyword fallback + WS→HTTP; sede desplegable.

## Estado previo — BrasAI = manuales; Agente = ops en vivo
- **BrasAI:** solo RAG (lealtad, alérgenos, merma, pedidos-manual).
- **Agente:** MCP `query_suppliers` + `query_inventory_ops`.

## Estado previo — BrasAI proxy timeout vs login OK
- Login OK (rápido); BrasAI fallaba: proxy cortaba a **10s** la query RAG.
- Proxy: probe `/health` → forward **120s** en `/knowledge` `/rfp` `/agent`.

## Estado previo — login timeout /api-backend
- Causa: `.env` con `INTERNAL_API_URL=http://backend:8000` pisaba host-gateway → login 12s abort.
- Compose **fuerza** `INTERNAL_API_URL=http://host.docker.internal:8000`.

## Estado previo — proxy BrasAI vía host-gateway
- Diagnóstico Codespaces: DNS `backend` OK, misma red, pero **TCP interfaces→backend:8000 = TIMEOUT**; host→`:8000` sí responde.
- `extra_hosts: host-gateway`; proxy IPv4 + fallbacks.
- **No** es por puerto 8000 Public/Private. Login: **`/api-backend`**.

## Estado previo — embed offline + API proxy Codespaces
- FastEmbed falla sin DNS a HuggingFace → `EMBEDDING_PROVIDER=hash` (compose default) + fallback automático.
- Backoffice Codespaces: API base **`/api-backend`** (ignora …-8000 guardado); WS agente sigue en puerto 8000 público.
- BrasAI: reindex + timeout; RFP markitdown OK tras rebuild.

## Estado previo — BrasAI + RFP + EUR
- **BrasAI** (ex Base de conocimiento); timeout UI + fallback grounded si falla el LLM.
- RFP: `markitdown[pdf]` en `services/api/requirements.txt` (faltaba en la imagen Docker).
- Proveedores: **todo en EUR (€)** con conversión COP/USD al validar/sembrar; `seed.py --force`.
- Alias `LLM_*` → `GENERATION_*`; Cambiar contraseña en Mi cuenta.

## Estado previo — candidaturas + Redis
- **Causa «Enviando…» en /trabaja-con-nosotros:** rewrite Next → `backend:8000` colgaba; website usa Route Handler `/api-backend` + timeout 15s (igual que backoffice).
- **Causa Flower/worker `Timeout connecting to redis`:** Redis con `--protected-mode yes` sin password rechaza clientes de otros contenedores → `protected-mode no` + healthcheck; worker/flower esperan `service_healthy`.
- **Website:** sin Google Fonts (stacks locales); evita reintentos a fonts.googleapis.com en Docker.
- **Hydration `bis_skin_checked`:** extensión del navegador muta el DOM; `suppressHydrationWarning` en html/body (website + backoffice). No es bug de Brasaland.
- **Favicon:** icono brasa/parrilla (terracotta sobre carbón) en website y backoffice.
- **BuildKit / disco:** `scripts/codespace-free-disk.sh` (NO borrar `.md` ≈5MB); si sigue lleno → Rebuild container. También `scripts/docker-rebuild-clean.sh`.
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
- Website: en Codespaces el browser llama `…-8000.app.github.dev` (igual que backoffice); en local `/api-backend` (proxy Node IPv4).
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
