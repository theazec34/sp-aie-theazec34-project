# Notificaciones SSE — tickets RFP en tiempo real

Capa de comunicación push para el dashboard `/rfp`. **No** invoca modelos ni agentes: solo publica cuando se registra un ticket (y, opcionalmente, alertas de umbral de ventas).

## Piezas

| Pieza | Ubicación |
|-------|-----------|
| Hub in-process + replay | `services/api/app/rfp/sse_hub.py` |
| HTTP | `GET /rfp/events/stream` (JWT), `POST /rfp/events/sales-drop-alert` |
| Cliente | `uis/backoffice/src/lib/rfpSse.ts` (`fetch` + `ReadableStream`) |
| UI | `uis/backoffice/src/app/rfp/page.tsx` |
| Tests | `services/api/tests/test_rfp_sse.py` |

## Eventos nombrados

### `rfp_ticket_created` (obligatorio)

Emitido en `POST /rfp/tickets` tras persistir el ticket en estado `analizando`.

Payload (campos BRIEFING / ticket existente):

```json
{
  "ticket_id": 12,
  "status": "analizando",
  "original_filename": "brasaland-request-1.pdf",
  "client_name": null,
  "location": null,
  "service_type": null,
  "scope": null,
  "deadline": null,
  "budget_range": null,
  "departments_needed": [],
  "created_at": "2026-10-20T10:00:00+00:00",
  "currency": "EUR",
  "currency_symbol": "€"
}
```

### `sales_drop_alert` (opcional)

Umbral de negocio: caída de ventas ≥ 15% vs semana anterior. Notifica a Mariana Restrepo y Felipe Guerrero. Mismo stream SSE.

```json
{
  "country": "CO",
  "drop_pct": 18.2,
  "threshold_pct": 15.0,
  "week_label": "2026-W42",
  "notify": ["Mariana Restrepo", "Felipe Guerrero"],
  "created_at": "…"
}
```

## Auth

Mismo JWT que el backoffice (`Authorization: Bearer …`). `EventSource` nativo **no** envía headers custom → el cliente usa `fetch` + `ReadableStream`.

Headers SSE: `Content-Type: text/event-stream`, keep-alive con frames comentario (`: keepalive`).

## Recuperación y dedupe

1. Cliente guarda `Last-Event-ID` en `sessionStorage`.
2. Al reconectar envía el header; el hub hace **replay corto** (últimos ~100 eventos) de ids mayores.
3. Tras abrir el stream, el cliente hace **refetch** de `GET /rfp/tickets`.
4. Dedupe UI: `markTicketSeen(ticket_id)` + merge por `ticket_id` en la lista.

## Reconexión

Backoff progresivo: `1s × 2^n` acotado a 30s. Indicador de estado en la UI (`En vivo` / `Reconectando…`).

## Verificación manual (red)

1. Abrir `/rfp` autenticado → badge «En vivo».
2. En otra sesión (o `curl` con JWT) subir un PDF → toast «Nuevo ticket RFP #…» sin F5.
3. DevTools → Network → Offline unos segundos → badge «Reconectando…» → Online → backoff + refetch sin duplicar filas.

## Preguntas de diseño (PR)

### 1. ¿Conexiones independientes o capa intermedia? ¿50 usuarios?

Cada dashboard abre una conexión SSE independiente al proceso API. El hub hace fan-out in-memory a colas por suscriptor. Con ~50 clientes en **un solo worker uvicorn** es viable (conexiones largas + keep-alive ligero). Si se escala a varios workers/procesos, el pub/sub in-process **no** cruza procesos: haría falta Redis Pub/Sub (u otro bus) delante del hub. Hoy no hay broker compartido a propósito (simplicidad del hito).

### 2. Estrategia de recuperación y anti-duplicados

**Last-Event-ID + replay corto + refetch-then-SSE.** Replay cubre huecos breves; el refetch de la lista cubre huecos fuera del buffer. La UI deduplica por `ticket_id` (set en sessionStorage + merge de lista).

### 3. ¿Por qué SSE y no WebSockets?

El flujo es **unidireccional** (servidor → cliente): aviso de ticket nuevo / alerta. SSE es HTTP/1.1 compatible, fácil de autenticar con el mismo stack FastAPI, y se reintegra con proxies vía `text/event-stream`. WebSockets aportan canal bidireccional y framing propio; pasarían a ser la herramienta correcta si hiciera falta **enviar** comandos por el mismo socket (chat, presencia, ACK de negocio en el canal), o multiplexar muchos tipos de tráfico interactivo. Para “hay un ticket nuevo” SSE basta.

## Pruebas

```bash
cd services/api && uv run pytest tests/test_rfp_sse.py -q
```

Cubre: `text/event-stream`, `event: rfp_ticket_created`, JSON en `data:`, 401 sin JWT, replay `Last-Event-ID`, alert opcional.
