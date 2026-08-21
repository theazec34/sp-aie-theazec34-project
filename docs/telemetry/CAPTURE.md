# Telemetry Capture — notas de implementación

**Rama:** `cursor/telemetry-capture-c620`  
**CONTEXT:** `CONTEXT-brasaland.es.telemetria.md` + plan en `telemetry-plan.md`

## Qué se entregó

| Capa | Pieza |
|------|--------|
| API stub | `POST /telemetry/events` → `{ received: N }` (sin DB) |
| Modelo | `TelemetryEvent` (envelope Phase 1) |
| Env BE | `TELEMETRY_ENDPOINT` |
| Env FE | `NEXT_PUBLIC_TELEMETRY_ENDPOINT` |
| Service | `uis/backoffice/src/services/telemetry.ts` — `track()` único, cola, batch 10s/20, sendBeacon, retry×3 |
| Instrumentación | 6 métricas CONTEXT + auth + nav + errores + latency + web vitals + rechazo edición stock |

## Verificar en DevTools

1. API: `uv run uvicorn app.main:app --reload --port 8000`
2. Backoffice: `NEXT_PUBLIC_TELEMETRY_ENDPOINT=http://localhost:8000/telemetry/events npm run dev`
3. Login / crear entrada-salida → Network: `POST .../telemetry/events` con `{ events: [...] }` y **200**.

## Separación perfil vs uso

- Perfil (nombre, email, rol) → TinyDB / `/auth/me`  
- Uso → solo eventos append-only vía `track()` (sin email/password en properties)
