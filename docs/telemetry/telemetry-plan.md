# Plan de Telemetría — Brasaland Digital (Inventario)

**Tipo:** diseño (sin instrumentación de código en este hito)  
**Rama:** `telemetria`  
**CONTEXT:** [`CONTEXT-brasaland.es.telemetria.md`](./CONTEXT-brasaland.es.telemetria.md)  
**Schemas:** [`event-schemas.json`](./event-schemas.json) (JSON Schema draft-07)  
**Fecha:** 2026-08-12  

**Mapeo código actual ↔ vocabulario CONTEXT**

| CONTEXT | Código monorepo (`services/api` / backoffice) |
|---------|-----------------------------------------------|
| `Product` | `Ingredient` (`/inventory/products`) |
| `InboundOrder` | `IngredientEntry` (`POST /inventory/orders/inbound`) |
| `OutboundOrder` | `IngredientExit` (`POST /inventory/orders/outbound`) |
| `location` | `location_id` (1–14) + `country` del ingrediente (`CO`/`US`) |
| `supplier` | `supplier_name` en entrada (hoy string); directorio `/suppliers` |

Umbral mínimo de stock usado hoy en UI: `LOW_STOCK_THRESHOLD = 10` (y vacío ≤ 0). El plan trata el umbral como **configurable por local** a futuro; el valor emitido va en `properties.threshold`.

---

## 0. Regla de oro

Cada evento existe solo si completa:

> Capturamos **`[event_type]`** porque necesitamos saber **`[hipótesis]`**, lo que permite la decisión **`[decisión concreta]`**.

---

## 1. Event Envelope (estándar)

Todos los eventos comparten el mismo sobre. Los payloads específicos viven solo en `properties` y están **allowlisteados** por `event_type`.

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `eventId` | `string` (UUID v4) | sí | Id único del evento |
| `timestamp` | `string` (ISO 8601 UTC) | sí | Momento de emisión, p.ej. `2026-08-12T17:30:00.000Z` |
| `sessionId` | `string` (UUID) | sí* | Sesión de backoffice (`localStorage`); `null` solo en jobs batch server-side documentados |
| `userId` | `string` | sí* | Id TinyDB del usuario como string (p.ej. `"1"`), **nunca email/nombre** |
| `event_type` | `string` | sí | Taxonomía `entity_action` (snake_case) |
| `schemaVersion` | `string` | sí | SemVer del envelope+allowlist, p.ej. `"1.0.0"` |
| `requestId` | `string` (UUID) | sí | Correlación FE↔BE (header `X-Request-Id`) |
| `properties` | `object` | sí | Payload allowlisteado; sin claves extra |

\*Excepción: `api_latency_recorded` emitido solo en middleware puede omitir `sessionId` si la request no autenticó (`userId` = `null`, `sessionId` = `null`).

**No se emiten:** email, nombre, teléfono, tokens JWT, passwords, cuerpos CSV de clientes.

---

## 2. Fase 1 — Catálogo de oportunidades

### 2.1 Mapa del flujo inventario (instrumentación)

```text
Login JWT → Dashboard / Inventario
  → GET /inventory/products (listado stock)
  → POST /inventory/orders/inbound  (entrada proveedor)
  → POST /inventory/orders/outbound (consumo | merma)
  → [rechazo] stock insuficiente / validación
  → [rechazo] intento de editar current_stock
  → [derivado] umbral mínimo / varianza de precio
```

**≥ 5 puntos de instrumentación (inventario)**

| # | Punto | Dónde emitir | Eventos |
|---|-------|--------------|---------|
| 1 | Entrada creada OK | API tras `POST .../inbound` 201 | `inbound_order_created` (+ opcional `ingredient_price_variance_detected`) |
| 2 | Salida consumo OK | API tras `POST .../outbound` con `reason=consumption` | `outbound_order_created` |
| 3 | Merma registrada | API tras outbound `reason=waste` | `stock_waste_registered` |
| 4 | Stock bajo umbral | API tras inbound/outbound si `current_stock < threshold` | `stock_threshold_triggered` |
| 5 | Validación / stock insuficiente | API 400 en outbound o validación Pydantic | `inventory_validation_failed`, `outbound_order_rejected` |
| 6 | Intento editar stock directo | API si llega PATCH/PUT con `current_stock` o ruta no expuesta | `direct_stock_edit_rejected` |

### 2.2 Eventos obligatorios (CONTEXT)

#### `inbound_order_created` — **obligatorio**

> Capturamos **`inbound_order_created`** porque necesitamos saber **cuánto y qué se compra por local y proveedor**, lo que permite **consolidar compras y negociar tarifas (Lucía)**.

- **Disparo:** `POST /inventory/orders/inbound` → 201  
- **Entrega:** **batch** horario + flush diario (urgencia comercial semanal; no requiere alerta en segundos)  
- **properties (allowlist):** ver §3  

#### `outbound_order_created` — **obligatorio**

> Capturamos **`outbound_order_created`** porque necesitamos saber **ritmo de consumo por ingrediente y local**, lo que permite **ajustar sugerencias de pedido a proveedores (Felipe)**.

- **Disparo:** outbound con `reason=consumption`  
- **Entrega:** **batch** (misma tubería que entradas)  

#### `stock_waste_registered` — **obligatorio**

> Capturamos **`stock_waste_registered`** porque necesitamos saber **cuánto se pierde, por qué y en qué local**, lo que permite **priorizar auditorías de merma (Felipe)**.

- **Disparo:** outbound con merma (`reason` de negocio ∈ `expired` \| `kitchen_error` \| `theft_suspected`)  
- **Nota de implementación:** hoy la API solo acepta `consumption` \| `waste`. En captura, mapear `waste` → exigir `waste_reason` en el cliente o ampliar el enum antes de instrumentar.  
- **Entrega:** **stream** (alerta operativa el mismo día)  

#### `stock_threshold_triggered` — **obligatorio**

> Capturamos **`stock_threshold_triggered`** porque necesitamos saber **con qué frecuencia un local se queda corto**, lo que permite **ajustar umbral o reabastecimiento**.

- **Disparo:** tras cualquier orden que deje `current_stock < threshold` (cruzando el umbral hacia abajo)  
- **Entrega:** **stream** (alerta a ops)  
- **Throttle:** máx. 1 evento / (`product_id`,`location_id`) / 15 min  

#### `direct_stock_edit_rejected` — **obligatorio**

> Capturamos **`direct_stock_edit_rejected`** porque necesitamos saber **si el personal intenta saltarse la trazabilidad**, lo que permite **reforzar capacitación/permisos (Jake)**.

- **Disparo:** request que intente mutar `current_stock` fuera de órdenes (ruta inexistente, campo extra, o UI deshabilitada que aún envía el campo) → 4xx  
- **Entrega:** **stream** (señal de cumplimiento)  

#### `ingredient_price_variance_detected` — **obligatorio**

> Capturamos **`ingredient_price_variance_detected`** porque necesitamos saber **cuándo el costo unitario se desvía >10% del histórico producto/proveedor**, lo que permite **alertar a Lucía/Mariana para renegociar**.

- **Disparo:** al crear inbound, si `|unit_cost - baseline| / baseline >= 0.10`  
- **Gap actual:** `IngredientEntry` aún no persiste `unit_cost`/`currency`; la instrumentación requerirá ampliar el schema de entrada (fuera de este hito de diseño).  
- **Entrega:** **stream**  

**Campos mínimos CONTEXT en inventario** (además del envelope):  
`location_id`, `country`, `product_id`, `product_category`, `quantity`, `unit`, `currency`; en merma además `reason`.

---

### 2.3 Oportunidades identificadas (técnicas + negocio)

#### Auth / sesión

| event_type | Origen | Hipótesis → decisión | Entrega |
|------------|--------|----------------------|---------|
| `auth_login_succeeded` | `POST /auth/login` 200 | Saber volumen de sesiones ops → dimensionar soporte y horarios pico | batch |
| `auth_login_failed` | login 401 | Detectar fuerza bruta / mala config de URL API → rate-limit o guía UX | **stream** |
| `auth_session_expired` | FE 401 en `apiFetch` con token presente | Flujos rotos por JWT corto → ajustar TTL o refresh | batch |

> Capturamos **`auth_login_failed`** porque necesitamos saber **cuántos fallos diarios hay y desde qué contexto**, lo que permite **decidir si reforzar rate-limit o mejorar el diagnóstico “Failed to fetch”**.

#### Inventario / validación (extra)

| event_type | Origen | Hipótesis → decisión | Entrega |
|------------|--------|----------------------|---------|
| `outbound_order_rejected` | outbound 400 stock insuficiente | Fricción en cocina por stock desfasado → priorizar sync/umbrales | **stream** |
| `inventory_validation_failed` | 422/400 Pydantic (qty≤0, location, reason) | Errores de formulario recurrentes → mejorar UX/validación FE | batch |
| `product_created` | `POST /inventory/products` 201 | Catálogo crece sin control → gobernanza de SKUs | batch |
| `inventory_products_viewed` | mount de `/inventory/products` | Qué locales/ops miran stock vs actúan → priorizar UX listado | batch |

#### Performance

| event_type | Origen | Hipótesis → decisión | Entrega |
|------------|--------|----------------------|---------|
| `api_latency_recorded` | middleware timing (ya existe log) | Endpoints lentos bajo carga → cache/índices | batch (sample) |

> Capturamos **`api_latency_recorded`** porque necesitamos saber **p95 de `/inventory/*`**, lo que permite **decidir si ampliar cache TTL o índices SQL**.  
> **Throttle:** sample 10% o 1/s por ruta.

#### Errores FE

| event_type | Origen | Hipótesis → decisión | Entrega |
|------------|--------|----------------------|---------|
| `frontend_error_captured` | `window.onerror` / ErrorBoundary backoffice | Bugs silenciosos en inventario → priorizar fixes | **stream** |

Sin stack traces con secrets; solo `error_name`, `message` sanitizado, `route`.

#### Navegación / abandono

| event_type | Origen | Hipótesis → decisión | Entrega |
|------------|--------|----------------------|---------|
| `page_viewed` | cambio de ruta App Router | Secciones más usadas → foco de producto | batch |
| `flow_abandoned` | salida de `/inventory/orders/inbound\|outbound` sin submit tras interacción | Formularios confusos → simplificar alta | batch |

> Capturamos **`flow_abandoned`** porque necesitamos saber **qué flujos de orden se dejan a medias**, lo que permite **rediseñar el formulario con más fricción percibida**.

---

### 2.4 Resumen de conteo

| Clasificación | Cantidad | event_types |
|---------------|----------|-------------|
| **Obligatorios (CONTEXT)** | **6** | `inbound_order_created`, `outbound_order_created`, `stock_waste_registered`, `stock_threshold_triggered`, `direct_stock_edit_rejected`, `ingredient_price_variance_detected` |
| **Oportunidades** | **12** | `auth_login_succeeded`, `auth_login_failed`, `auth_session_expired`, `outbound_order_rejected`, `inventory_validation_failed`, `product_created`, `inventory_products_viewed`, `api_latency_recorded`, `frontend_error_captured`, `page_viewed`, `flow_abandoned`, `supplier_directory_viewed` |
| **Total diseñado** | **18** | |

Categorías cubiertas: **negocio/inventario**, **autenticación**, **performance**, **errores**, **navegación**.

*(Se añade `supplier_directory_viewed` como oportunidad ligera de navegación ops compras — ver §3.)*

---

## 3. Esquemas por evento (allowlist de `properties`)

Leyenda: **R** = required, **O** = optional.

### 3.1 Inventario (obligatorios + afines)

#### `inbound_order_created`

| property | tipo | | descripción |
|----------|------|--|-------------|
| `location_id` | integer 1–14 | R | Local |
| `country` | `CO`\|`US` | R | País del local/ingrediente |
| `product_id` | integer | R | Id ingrediente |
| `product_sku` | string | O | SKU estable para agregaciones |
| `product_category` | string | R | meat/produce/… |
| `quantity` | number >0 | R | Cantidad entrada |
| `unit` | string | R | kg\|litro\|unidad |
| `currency` | `COP`\|`USD` | R | Moneda del local (sin conversión) |
| `unit_cost` | number | O | Costo unitario (cuando exista en API) |
| `supplier_id` | string\|null | O | Si se enlaza a `/suppliers` |
| `supplier_name` | string | R | Nombre proveedor (tal cual API) |
| `order_id` | integer | R | Id `IngredientEntry` |
| `city` | string | O | Ciudad del local (catálogo 14 sedes) |

#### `outbound_order_created`

Igual que entrada en local/producto/qty/unit/currency, más:

| property | tipo | | descripción |
|----------|------|--|-------------|
| `reason` | `consumption` | R | Solo consumo (merma va a otro evento) |
| `order_id` | integer | R | Id exit |

#### `stock_waste_registered`

| property | tipo | | descripción |
|----------|------|--|-------------|
| `location_id`, `country`, `product_id`, `product_category`, `quantity`, `unit`, `currency` | (igual) | R | |
| `reason` | `expired`\|`kitchen_error`\|`theft_suspected` | R | Taxonomía CONTEXT |
| `order_id` | integer | R | |

#### `stock_threshold_triggered`

| property | tipo | | descripción |
|----------|------|--|-------------|
| `location_id`, `country`, `product_id`, `product_category`, `unit` | | R | |
| `current_stock` | number | R | Stock tras la operación |
| `threshold` | number | R | Umbral configurado (hoy default 10) |
| `triggering_order_kind` | `inbound`\|`outbound` | R | Qué movimiento cruzó el umbral |
| `triggering_order_id` | integer | R | |

#### `direct_stock_edit_rejected`

| property | tipo | | descripción |
|----------|------|--|-------------|
| `location_id` | integer\|null | O | Si venía en body |
| `country` | string\|null | O | |
| `product_id` | integer\|null | O | |
| `attempted_field` | string | R | p.ej. `current_stock` |
| `http_status` | integer | R | 400/404/405 |
| `route` | string | R | path intentado |

#### `ingredient_price_variance_detected`

| property | tipo | | descripción |
|----------|------|--|-------------|
| `location_id`, `country`, `product_id`, `product_category`, `unit`, `currency` | | R | |
| `supplier_name` | string | R | |
| `unit_cost` | number | R | Costo de la orden actual |
| `baseline_unit_cost` | number | R | Mediana/media histórica |
| `variance_pct` | number | R | `(unit_cost-baseline)/baseline` |
| `threshold_pct` | number | R | Default `0.10` |
| `order_id` | integer | R | Inbound asociado |

#### `outbound_order_rejected` / `inventory_validation_failed` / `product_created`

Ver `event-schemas.json` (allowlists estrictas: `error_code`, `field`, `message_key` — **no** mensajes libres con PII).

### 3.2 Auth, perf, errores, navegación

Documentados campo a campo en `event-schemas.json` (`$defs`). Resumen:

- Auth: `result`, `failure_reason` ∈ `bad_credentials`\|`inactive`\|`network`\|`unknown` — sin password/email.  
- Latency: `route`, `method`, `status_code`, `duration_ms`, `cache_status`.  
- FE error: `route`, `error_name`, `message_sanitized`.  
- Nav: `route`, `referrer_route`, `dwell_ms` (abandon).

---

## 4. Fase 3 — Estrategia de entrega

| Criterio | Stream | Batch |
|----------|--------|-------|
| ¿Ops debe actuar en minutos/horas? | sí | no |
| ¿Alimenta dashboard semanal Mariana? | opcional | sí |
| Volumen alto / ruido | throttle | agregar |

**Stream:** `stock_waste_registered`, `stock_threshold_triggered`, `direct_stock_edit_rejected`, `ingredient_price_variance_detected`, `auth_login_failed`, `outbound_order_rejected`, `frontend_error_captured`.

**Batch:** órdenes inbound/outbound de consumo, vistas de página, logins OK, latencias muestreadas, `product_created`, abandonos (agregar diario).

**Throttle / debounce**

| Evento | Política |
|--------|----------|
| `stock_threshold_triggered` | 1 / (product, location) / 15 min |
| `api_latency_recorded` | sample 10% o max 1/s·ruta |
| `page_viewed` | debounce 1s por ruta |
| `frontend_error_captured` | 1 / (error_name, route) / 5 min |
| `auth_login_failed` | sin sample; rate-limit emisión 20/min·IP hasheada (solo hash, no IP raw en properties) |

Pipeline objetivo (vendor-agnóstico): FE/BE → cola stream (alertas) + sink batch (Parquet/CSV diario) → agregaciones por `location_id`, `country`, semana ISO.

---

## 5. Privacidad y sanitización

| Dato | Tratamiento |
|------|-------------|
| Email / nombre / teléfono | **No emitir** |
| JWT / passwords | **No emitir** |
| `userId` | Id opaco TinyDB string |
| IP | No en properties; si se usa para rate-limit, hash one-way solo en capa infra |
| `supplier_name` / `product_sku` | Permitidos (dato operativo, no PII persona) |
| Mensajes de error | Claves (`message_key`) o texto recortado sin email |

---

## 6. Riesgos, exclusiones y descartes

### Considerados y **descartados**

| Candidato | Por qué no |
|-----------|------------|
| `employee_name_entered` | PII; CONTEXT lo prohíbe |
| Telemetría del **website público** (carta/formulario) | Fuera del RFI de inventario ops; coste/ruido |
| `csv_incident_analyzed` | Dominio incidencias postventa, no inventario |
| Cada keystroke en formularios | Coste, privacidad, sin decisión clara |
| Conversión COP↔USD en el evento | CONTEXT: la conversión es del pipeline ejecutivo, no de telemetría |

### No capturado aún (gaps de producto)

- `unit_cost` en entradas (necesario para varianza de precio).  
- Sub-razones de merma (`expired` / …) vs enum actual `waste`.  
- Umbral mínimo **por local** (hoy constante UI).

### Riesgos

- Doble conteo si FE y BE emiten el mismo `event_type` → **fuente de verdad = BE** para órdenes; FE solo nav/errores.  
- `requestId` ausente → generar UUID en middleware si falta header.  
- Alert fatigue en `stock_threshold_triggered` → throttle obligatorio.

---

## 7. Datos semilla sugeridos (para hitos posteriores de captura)

Al instrumentar/probar:

- 8–10 productos (≥3 categorías)  
- 3 locales (mín. 1 CO y 1 US)  
- 15–20 inbound / 15–20 outbound (≥3 mermas con razones distintas)  
- ≥2 cruces de umbral y ≥1 varianza de precio >10%  

---

## 8. Guía de implementación (para el siguiente desarrollador)

1. Añadir middleware que asegure `X-Request-Id` y reutilice `api.timing`.  
2. Tras commits de inventario, llamar `telemetry.emit(event_type, properties)` validando allowlist (`event-schemas.json`).  
3. En backoffice: `sessionId` UUID en `localStorage`; enviar `X-Session-Id` + `X-Request-Id`.  
4. No loguear PII; tests que fallen si `properties` tiene claves fuera de allowlist.  
5. Ampliar API: `unit_cost`+`currency` en inbound; `waste_reason` en merma — **antes** de dar por cerrada la captura de métricas CONTEXT.

---

## 9. Checklist de evaluación (auto)

- [x] 6 métricas obligatorias CONTEXT presentes  
- [x] Oportunidades técnicas y de negocio (≥ auth, perf, errores, nav)  
- [x] Hipótesis → decisión en cada evento  
- [x] Envelope uniforme con campos requeridos  
- [x] Allowlist por evento  
- [x] `event-schemas.json` alineado al plan  
- [x] Stream/batch justificados por urgencia de negocio  
- [x] PII sanitizada  
- [x] Riesgos / exclusiones  
- [x] Suficientemente preciso para implementar sin reinterpretar el CONTEXT  
