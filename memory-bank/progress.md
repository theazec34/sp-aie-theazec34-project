# Progress — Brasaland Digital

## Estado (2026-10-20)
- **`main`:** PRs **#1–#46** (SSE RFP #46 mergeado).
- **Hito en curso:** **WebSocket chat** — Manager support agent Parte 2/2 (`cursor/websocket-chat-c620`).
- **Moneda RFP:** **euros (€)**.
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## WebSocket chat (hito actual)
- `WS /agent/chat/ws` — JWT `?token=` / frame auth; `session_id` = thread_id
- Pub/Sub in-process `chat.<session_id>`; productor desacoplado de consumidores
- Eventos: `token_chunk`, `interrupt_requested`, `generation_interrupted`, `generation_completed`, `session_snapshot`, `user_message`
- Abort real de emisión (no HITL `interrupt()`); mensaje parcial `interrupted`
- UI backoffice `/agent` — tokens en vivo, interrupción, backoff + rehidratación
- Docs: `docs/realtime/websocket-chat.md`, BRIEFING `docs/realtime/brasaland-BRIEFING.es-2-2.md`
- Tests: `services/api/tests/test_agent_chat_ws.py`

## SSE notificaciones (en main)
- #46 — `rfp_ticket_created` + UI `/rfp`

## RFP Partes 1–3 (en main)
- #42 · #44 · #45

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#45 |
| SSE notificaciones RFP | #46 |
| WebSocket agent chat | este PR |
