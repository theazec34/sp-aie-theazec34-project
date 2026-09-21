# DEV-55 — Async tasks (Celery + Redis)

## Endpoint convertido
`POST /api/v1/incidents/analyze` — análisis CSV de incidencias (antes síncrono y bloqueante).

**Por qué:** parseo + reglas de validación sobre CSVs grandes; no debe bloquear el event loop de FastAPI. El mensaje Celery solo lleva `upload_id` (el worker lee el fichero en disco).

## Flujo
Cliente → API (202 + `task_id`) → Redis → Worker → resultado en Redis → `GET /tasks/{task_id}`.

## Demo local (2026-09-21)
- SUCCESS: `aba8d4a4-f38c-463c-87b4-b17337651cbf`
- FAILURE → DLQ: `fce089c8-3fae-45d4-bdf4-7b73f9602373` (attempt 4)
- Retry log:

```
analyze_retry task_id=fce089c8-... attempt=1 countdown=2s error=RuntimeError: Forced failure...
analyze_retry ... attempt=2 countdown=4s ...
analyze_retry ... attempt=3 countdown=8s ...
DLQ recorded task_id=fce089c8-... attempt=4 error=RuntimeError: Forced failure...
```

Flower: http://localhost:5555 (screenshot en artefactos del agente).
