# Telemetry Report — notas de implementación

**Rama:** `cursor/telemetry-report-c620`  
**PR título exigido:** `feat: telemetry report endpoint`

## Piezas

| Capa | Ruta |
|------|------|
| Pipeline Pandas | `services/telemetry/analysis.py` |
| Re-export API | `services/api/app/telemetry/analysis.py` |
| Endpoint | `GET /telemetry/report?start_date=&end_date=` |
| Cache | `telemetry_report_cache` TTL **60s** (`app/cache.py`) |
| Dashboard | `uis/backoffice` → `/telemetry` |
| Seed local | `python seed_telemetry.py` (≥20 eventos mixtos) |

## Métricas (pregunta operativa)

| Métrica | Pregunta |
|---------|----------|
| `events_per_day` | ¿Cuántos eventos de telemetría llegan por día? |
| `error_rate_by_type` | ¿Qué proporción del tráfico diario es cada tipo de error técnico? |
| `auth_failure_rate` | ¿Qué % de intentos de login fallan cada día? |
| `latency_by_route` | ¿Cuál es la latencia media diaria por ruta de API? |

## Ejemplo

```bash
cd services/api && python seed_telemetry.py
curl -s 'http://localhost:8000/telemetry/report' | python -m json.tool
```
