# Progress — Brasaland Digital

## Estado (2026-10-20)
- **`main`:** PRs **#1–#45** (RFP Parte 3 #45 mergeado).
- **Hito en curso:** **Notificaciones SSE** — tickets RFP en tiempo real (`feature/sse-notifications`).
- **Moneda de producto RFP/propuestas:** **euros (€)**.
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## SSE notificaciones (hito actual)
- Hub in-process + replay `Last-Event-ID`: `services/api/app/rfp/sse_hub.py`
- `GET /rfp/events/stream` (JWT, `text/event-stream`, evento `rfp_ticket_created`)
- Opcional: `sales_drop_alert` + `POST /rfp/events/sales-drop-alert`
- UI: `fetch` + ReadableStream, backoff, dedupe, badge «En vivo» en `/rfp`
- Docs: `docs/rfp/sse-notifications.md` (respuestas de diseño)
- Tests: `services/api/tests/test_rfp_sse.py`
- **Sin** llamadas a modelos/agentes en esta capa

## RFP Partes 1–3 (en main)
- #42 intake · #44 generación · #45 aprobación HITL + €

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#44 |
| RFP aprobación Parte 3 + € | #45 |
| SSE notificaciones RFP | #46 |
