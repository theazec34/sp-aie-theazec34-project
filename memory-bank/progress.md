# Progress — Brasaland Digital

## Estado (2026-09-21)
- **`main` actualizado:** PRs **#1–#21**, **#23–#35** (RAG #35 + review #34 mergeados).
- **Hito en curso:** Celery/Redis **DEV-55** — rama `cursor/async-tasks-celery-c620`.
- **Auditoría rápida:** sin Celery previo; RAG ya en main; docs memory-bank alineadas en este PR.
- **Fuera de alcance:** `hito-3` / `3.5`, `brasaland_agent`.

## DEV-55 (async tasks)
- Redis en Compose (`noeviction`) + Flower `:5555` + worker independiente
- Endpoint async: `POST /api/v1/incidents/analyze` → **202** `{task_id}`
- Status: `GET /tasks/{task_id}` → `pending|started|success|failure`
- Retries: `max_retries=3` + backoff exponencial `2/4/8s`
- DLQ: tabla `celery_dead_letters` (task_id, attempt, error, timestamp)
- UI CSV (`uis/web`) hace poll de `/tasks/{id}`
- Tests: `services/api/tests/test_celery_tasks.py` (suite API **56 passed**)

## Hitos en main
| Área | PR |
|------|-----|
| Producto base + Docker + perf/cache | #1–#21 |
| Telemetría | #23–#26 |
| Pipeline | #27–#29 |
| Nightly | #30 |
| Sentimiento | #31 |
| Ventas ML | #32–#33 |
| Docs review | #34 |
| RAG knowledge | #35 |
| Celery DEV-55 | este PR |

## Arranque RAG / Celery
Ver `README.md` y `DOCKER.md`.
