# WebSocket chat — Manager support agent (Parte 2/2)

Capa de comunicación bidireccional sobre el agente existente. **No** rediseña nodos, tools ni memoria.

## Piezas

| Pieza | Ubicación |
|-------|-----------|
| Pub/Sub `chat.<session_id>` | `services/agent/chat/pubsub.py` |
| ChatSession store | `services/agent/chat/sessions.py` |
| Productor tokens + abort | `services/agent/chat/streamer.py` |
| WebSocket | `WS /agent/chat/ws` → `services/agent/chat/ws.py` |
| UI | `uis/backoffice` → `/agent` |
| Cliente | `uis/backoffice/src/lib/agentChatWs.ts` |
| BRIEFING | `docs/realtime/brasaland-BRIEFING.es-2-2.md` |
| Tests | `services/api/tests/test_agent_chat_ws.py` |

## Auth

Mismo JWT que backoffice / SSE Parte 1. En el handshake: `?token=` (preferido) o primer frame:

```json
{"event": "auth", "data": {"token": "<jwt>"}}
```

Sin JWT válido no hay eventos de chat.

## Sesión

`ChatSession`: `session_id`, `agent_id=manager_support`, `user_id`, `location_id`, `status` (`active`|`interrupted`|`closed`), `created_at`.

`session_id` del handshake = LangGraph `thread_id` (vía `run_agent(..., session_id=)`).

## Eventos (contrato)

```json
{"event": "token_chunk", "data": {"session_id": "chat_0044", "message_id": "msg_…", "token": "Para", "sequence": 12}}
{"event": "interrupt_requested", "data": {"session_id": "chat_0044", "new_input": "…"}}
{"event": "generation_interrupted", "data": {"session_id": "chat_0044", "message_id": "msg_…", "status": "interrupted"}}
{"event": "generation_completed", "data": {"session_id": "chat_0044", "message_id": "msg_…"}}
{"event": "session_snapshot", "data": {"session_id": "chat_0044", "messages": []}}
{"event": "user_message", "data": {"session_id": "chat_0044", "text": "…"}}
```

No se mezclan payloads RFP/SSE (`ticket_id`, `rfp_ticket_created`, etc.).

## Abort vs HITL

El abort de stream usa un `asyncio.Event` por `generation_id` en la capa de canal. **No** usa `interrupt()` de LangGraph (HITL). Tras abort: el mensaje assistant parcial queda con `status=interrupted`; el siguiente `user_message` / `new_input` abre un turno nuevo sin sobrescribirlo.

## Pub/Sub

Un productor (`run_streaming_turn`) publica al canal `chat.<session_id>`. N conexiones WS suscritas reciben el mismo evento — no se re-invoca el agente por spectator.

## Cómo probar

```bash
cd services/api && PYTHONPATH=. uv run pytest tests/test_agent_chat_ws.py -q
```

### Manual — interrupción

1. Abrir `/agent`, conectar (badge «En vivo»).
2. Enviar una pregunta larga.
3. Mientras «Escribiendo…», pulsar **Detener** o enviar otro mensaje.
4. El bubble assistant queda marcado **Interrumpido**; el nuevo turno aparece aparte.

### Manual — reconexión

1. Anotar `session_id` en la UI.
2. DevTools → Offline unos segundos → Offline off (backoff).
3. O recargar la página: el cliente reenvía el mismo `session_id` → `session_snapshot` con historial (no chat en blanco).

## Preguntas de diseño

### 1. ¿Por qué WebSocket y no SSE (Parte 1)?

La Parte 1 es **unidireccional** (servidor → cliente): avisar de un ticket. Aquí hace falta **bidireccionalidad en el mismo canal**: el encargado envía `user_message` / `interrupt_requested` mientras recibe `token_chunk`. SSE no transporta esos comandos de cliente sin un segundo canal HTTP.

### 2. ¿Varios clientes en la misma sesión?

Pub/Sub por `chat.<session_id>`: un productor por generación; N suscriptores WS. Un supervisor que abre el mismo `session_id` ve los mismos eventos sin duplicar `run_agent`.

### 3. Abort de stream vs `interrupt()` HITL

Abort = flag de generación en la capa de comunicación (deja de emitir `token_chunk`). HITL `interrupt()` pausaría el grafo a la espera de un humano — no aplica a “para, me equivoqué de local”. El mensaje parcial se conserva como `interrupted`; el siguiente input es un turno nuevo.
