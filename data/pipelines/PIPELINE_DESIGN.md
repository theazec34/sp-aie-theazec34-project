# PIPELINE_DESIGN — Brasaland Digital  
## Reporte Semanal de Costo y Merma por Local

**Tipo de hito:** diseño (sin orquestación Prefectora aún)  
**Rama:** `pipeline-design`  
**CONTEXT de negocio:** [`docs/pipelines/CONTEXT-brasaland.es.pipeline.md`](../../docs/pipelines/CONTEXT-brasaland.es.pipeline.md)  
**CONTEXT de telemetría (métricas obligatorias):** [`docs/telemetry/CONTEXT-brasaland.es.telemetria.md`](../../docs/telemetry/CONTEXT-brasaland.es.telemetria.md)  
**Fecha:** 2026-08-21  

> Este documento es la especificación del **pipeline de desempeño de negocio**.  
> No sustituye el reporte técnico de ingeniería (`services/telemetry/analysis.py`, `GET /telemetry/report`).

---

## Fase 1 — Estado actual y gap de negocio

### 1.1 Estado actual de la telemetría

| Pieza | Dónde vive | Qué responde hoy |
|-------|------------|------------------|
| Captura FE | `uis/backoffice` → `track()` / `TelemetryService` | Emite eventos de inventario + técnicos al sink |
| Almacenamiento | tabla `telemetry_events` (Supabase/SQLite) | Hechos append-only: `event_type`, `timestamp`, `tags` (JSONB), `event_id`, etc. |
| Reporte técnico | `services/telemetry/analysis.py` + `GET /telemetry/report` | Volumen diario, tasa de error por tipo, fallo de login, latencia por ruta |
| Dashboard ops | backoffice `/telemetry` | Vista de ingeniería (salud del sistema), no KPIs de margen |

**Eventos de inventario ya instrumentados (obligatorios CONTEXT telemetría):**

- `inbound_order_created`
- `outbound_order_created`
- `stock_waste_registered`
- `stock_threshold_triggered`
- `direct_stock_edit_rejected`
- `ingredient_price_variance_detected`

**Vocabulario del monorepo (no reinventar):**

| CONTEXT negocio | Código actual |
|-----------------|---------------|
| `Product` | `Ingredient` / `product_id` en tags |
| `InboundOrder` | `IngredientEntry` |
| `OutboundOrder` | `IngredientExit` |
| `location` | `location_id` entero **1–14** + `country` `CO`/`US` |
| Moneda | `COP` (CO) / `USD` (US) — sin conversión FX en v1 |

### 1.2 Qué ya responde el reporte técnico (ingeniería)

- ¿Hay tráfico de telemetría? → `events_per_day`
- ¿Qué errores técnicos dominan? → `error_rate_by_type`
- ¿Fallan los logins? → `auth_failure_rate`
- ¿Qué rutas van lentas? → `latency_by_route`

Esas preguntas son para el equipo de ingeniería. **No** responden a Mariana ni a Felipe.

### 1.3 Gap de negocio (por qué hace falta este pipeline)

Mariana (CEO) y Felipe (Ops) necesitan cada **lunes** un consolidado por local/país de **costo de compra, costo de merma, ratio de merma, quiebres de stock y alertas de precio**.

Ese entregable **no** existe hoy:

- `GET /telemetry/report` no agrega costos ni granula por `location_id` / semana ISO.
- `telemetry_events` es la fuente cruda; no es un almacén de KPIs de negocio.
- Sin una tabla en esquema `reporting` + un módulo `services/reporting/`, el liderazgo seguiría pidiendo exports manuales.

**Gap explícito:** pasar de eventos técnicos/operativos crudos a los **cinco KPIs** del CONTEXT de pipeline (sección 2), con grano `location_id` × `week_start`.

### 1.4 Extensión de captura requerida (aditiva, no evento nuevo)

Para calcular costos, `inbound_order_created` y `stock_waste_registered` deben llevar costo en `properties`:

| Evento | Campo aditivo | Uso |
|--------|---------------|-----|
| `inbound_order_created` | `unit_cost` (ya en allowlist; reforzar emisión) y/o `total_cost = quantity * unit_cost` | KPI costo de compra |
| `stock_waste_registered` | `unit_cost` y/o `total_cost` (añadir al schema/allowlist) | KPI costo de merma |

No se inventan `event_type` nuevos. No se escribe nunca de vuelta en `telemetry_events` desde el pipeline.
