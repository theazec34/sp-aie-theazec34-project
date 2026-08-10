# CACHING_REPORT — Brasaland Digital

Fecha: 2026-08-10  
Rama: `cursor/caching-optimisation-c620`  
Stack: FastAPI (`services/api`) + Next.js (`uis/website`, `uis/backoffice`)

---

## 0. Cómo medimos (evidencia)

Se añadió middleware de timing en `app/main.py` que registra:

`METHOD path -> status | X.Xms`

y expone `X-Response-Time-Ms` / `X-Cache` (HIT|MISS) en las rutas cacheadas.

Seeding realista (`services/api/seed_load.py`):

| Tabla | Filas tras seed |
|-------|-----------------|
| Incidents (TinyDB) | **800** (títulos/descripciones/categorías/sedes variadas) |
| Suppliers (TinyDB) | **40** (ciudades, tarifas, categorías y estados mixtos) |

Medición local (`uvicorn` en `127.0.0.1:8000`, n=40 hits):

| Endpoint | MISS (ms) | HIT median (ms) | HIT p95 (ms) |
|----------|-----------|-----------------|--------------|
| `GET /api/incidents/summary` | **2.5–4.9** | **0.3** | **0.8** |
| `GET /suppliers` | **1.8–2.5** | **1.1** | **1.7** |
| `GET /api/incidents` (sin cache, contraste) | median **5.8** (801 filas) | — | — |

En lab local TinyDB es rápido; el patrón sigue siendo claro: el dashboard/listado se pide muchas veces con la misma respuesta, y el HIT evita re-escanear + re-agregar. Bajo más filas o disco más lento el MISS sube y el beneficio relativo crece.

---

## 1. Decisiones frontend

### Lazy loading (≥ 2)

| Componente | Dónde | Por qué se aplaza |
|------------|-------|-------------------|
| `ApplicationForm` | `uis/website/src/app/page.tsx` via `next/dynamic` | Formulario cliente below-the-fold; no hace falta para LCP del hero/carta. Ya existía; se mantiene y documenta. |
| `GalleryGrid` | mismo `page.tsx` via `next/dynamic` | Galería con varios `next/image`; no crítica para primer viewport. Reduce JS/imágenes del path inicial. |
| `SupplierCreateForm` (extra) | `uis/backoffice/.../proveedores/page.tsx` | Formulario de alta pesado; el listado puede pintar antes de bajar el chunk. |

### `useMemo` (≥ 1, no trivial)

En `uis/backoffice/src/app/inventory/products/page.tsx`:

```ts
const rows = useMemo(() => items
  .map(item => ({ ...item, level, categoryLabel, countryLabel }))
  .sort((a, b) => LEVEL_ORDER[a.level] - LEVEL_ORDER[b.level] || name),
[items]);
```

**Beneficio:** en cada re-render del shell (loading flags, errores, clicks de “Actualizar”) se evitaba re-calcular nivel de stock + labels + orden por criticidad sobre toda la lista. Dependencias: solo `[items]`.

No se memoizaron booleans triviales (`hasErrors`, etc.).

---

## 2. Decisiones backend

### Evaluación rápida de endpoints

| Endpoint | Coste | Frecuencia | Estabilidad datos | ¿Cache? |
|----------|-------|------------|-------------------|---------|
| `GET /api/incidents/summary` | Alto (scan + 4 agregaciones) | Alta (dashboard `/incidents/resumen`) | Media (cambia en create/status) | **Sí** |
| `GET /suppliers` | Medio (list + filtros) | Alta (directorio compras) | Alta (pocas escrituras) | **Sí** |
| `GET /inventory/products` | Alto (stock calculado) | Alta | Baja (cambia en cada inbound/outbound) | No (TTL corto + invalidación posible; aplazado) |
| `GET /api/incidents` | Medio-alto (lista completa) | Media | Media | **No** (ver §4) |
| `GET /auth/me`, `/profiles/me` | Bajo | Alta | Por usuario | **No** (dato privado) |
| `POST /*` | Escritura | — | — | **No** |

### Caches implementados

Implementación: `app/cache.py` — diccionario in-process con TTL + invalidación por clave/prefijo (sin Redis; suficiente para un worker uvicorn).

#### 1) `GET /api/incidents/summary`

- **Coste:** O(n) sobre todas las incidencias + counters.
- **Frecuencia estimada:** cada visita/al refrescar el resumen; polling manual frecuente en ops.
- **TTL:** **30 s** (`INCIDENTS_SUMMARY_TTL`).
- **Clave:** `incidents:summary` (pública, misma para todos — sin PII).
- **Invalidación:** `POST /api/incidents` y `PATCH /api/incidents/{id}/status` llaman `incidents_cache.invalidate(...)`.
- **Header:** `X-Cache: HIT|MISS`.

#### 2) `GET /suppliers` (tras JWT)

- **Coste:** lectura TinyDB + filtros country/category.
- **Frecuencia:** listado de compras al abrir `/proveedores` y al cambiar filtros.
- **TTL:** **60 s** (`SUPPLIERS_LIST_TTL`).
- **Clave:** `suppliers:list:country={x}:category={y}` — **compartida entre usuarios autenticados** porque el directorio no es personal. Auth sigue siendo obligatoria antes de servir.
- **Invalidación:** create / rate / status / delete → `invalidate_prefix("suppliers:list:")`.
- **Header:** `X-Cache: HIT|MISS`.

Helpers: `GET /api/cache-stats` (hits/misses/entries, sin payloads).

---

## 3. Trade-offs frescura vs rendimiento

- **Summary TTL 30 s:** un dashboard puede mostrar totales hasta 30 s “viejos” si nadie escribe. En ops de restaurante eso es aceptable: las agregaciones no son saldo bancario. Cualquier alta o cambio de estado **invalida al momento**, así que el caso de escritura queda fresco.
- **Suppliers TTL 60 s:** el catálogo cambia poco; 1 minuto de tarifa/estado obsoleto en otra pestaña es tolerable, y las mutaciones desde el mismo backoffice invalidan el namespace.
- **In-process cache:** no se comparte entre múltiples workers/réplicas. Aceptable ahora; si se escala horizontal, el siguiente paso sería Redis con las mismas claves/TTL.

---

## 4. Qué NO se cacheó (y por qué)

1. **`GET /auth/me` / `GET /profiles/me`** — datos de sesión/PII. Una clave compartida sería fuga entre usuarios. Si algún día se cacheara, la clave debería incluir `user_id` y TTL muy corto; no aporta frente al coste actual.
2. **`GET /api/incidents` (lista)** — respuesta grande (~800 filas), muchos filtros posibles → muchas claves o claves demasiado genéricas. El beneficio MISS→HIT no compensa el riesgo de servir listados stale filtrados mal. Preferimos cachear el **summary** (barato de almacenar, caro de calcular).
3. **`POST /api/v1/incidents/analyze`** — el cuerpo es un CSV distinto cada vez; no hay reutilización.

---

## 5. Checklist de evaluación

- [x] ≥ 2 lazy loads documentados (`GalleryGrid`, `ApplicationForm`; extra `SupplierCreateForm`)
- [x] ≥ 1 `useMemo` no trivial (stock rows)
- [x] ≥ 2 endpoints con TTL (`/api/incidents/summary`, `/suppliers`)
- [x] Invalidación en escrituras
- [x] Sin datos privados en clave compartida
- [x] Este informe con trade-offs y “qué no cachear”

---

## 6. Cómo reproducir

```bash
cd services/api
uv run python seed_load.py          # carga realista
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
# repetir GET /api/incidents/summary y observar X-Cache + logs api.timing
uv run pytest tests/test_cache.py -q
```
