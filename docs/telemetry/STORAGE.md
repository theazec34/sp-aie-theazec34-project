# Telemetry Storage — notas de implementación

**Rama:** `cursor/telemetry-storage-c620`  
**Precondición:** captura mergeada (stub + `TelemetryService` + instrumentación)

## Qué se entregó

| Capa | Pieza |
|------|--------|
| SQL Supabase | `services/api/sql/telemetry_events.sql` — 8 columnas, índices (`timestamp`, `event_type`, GIN `tags`), triggers append-only |
| ORM | `app/telemetry/orm.py` — `TelemetryEventRow` (create_all / SQLite) |
| Endpoint | `POST /telemetry/events` — parseo por evento, bulk INSERT, `{ received, stored, rejected }` |
| Allowlist tags | `app/telemetry/allowlist.py` — propiedades CONTEXT + plan; sin PII |
| Modelo envelope | `TelemetryEvent` **sin cambios** respecto al hito de captura |
| Frontend | **sin cambios** — misma URL `NEXT_PUBLIC_TELEMETRY_ENDPOINT` |

## Columnas (`telemetry_events`)

`id`, `event_id`, `event_type`, `timestamp`, `service`, `session_id`, `user_id`, `tags`

`tags` = allowlist de `properties` + `schema_version` + `request_id`.

## Cómo aplicar en Supabase

1. SQL Editor → pegar y ejecutar `services/api/sql/telemetry_events.sql`
2. Confirmar `DATABASE_URL` (Transaction pooler) en `services/api/.env`
3. Reiniciar API (borrar `data/.sqlite_fallback` si existía un fallback previo)

## Verificar

```bash
# Lote mixto (1 válido + 1 inválido)
curl -s -X POST http://localhost:8000/telemetry/events \
  -H 'Content-Type: application/json' \
  -d '{"events":[{"eventId":"11111111-1111-4111-8111-111111111111","timestamp":"2026-08-21T12:00:00.000Z","sessionId":"22222222-2222-4222-8222-222222222222","userId":"1","event_type":"page_viewed","schemaVersion":"1.0.0","requestId":"33333333-3333-4333-8333-333333333333","properties":{"route":"/inventory"}},{"bad":true}]}'
# → {"received":2,"stored":1,"rejected":1}
```

En Supabase: `select event_type, timestamp, tags from telemetry_events order by timestamp desc limit 20;`
