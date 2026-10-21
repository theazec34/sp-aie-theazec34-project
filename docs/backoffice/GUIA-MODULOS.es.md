# Guía de módulos del backoffice (`:3001`)

Panel interno Brasaland. Requiere **login JWT** (admin del seed: `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` en `.env`).

**Antes de probar:**
1. Copia `.env.example` → `.env` en la raíz (obligatorio `SECRET_KEY`; sin ella el login/API autenticada responde **HTTP 500**).
2. API `:8000` + backoffice `:3001` (`docker compose up` o uvicorn + `npm run dev`).
3. En login usa URL **`/api-backend`** («Usar auto-detectada»).
4. El menú izquierdo sigue el mismo orden que las tarjetas del Panel.

Archivos de ejemplo: [`data/samples/backoffice/`](../../data/samples/backoffice/) y RFP en [`rfp-requests/brasaland/`](../../rfp-requests/brasaland/).

---

## Arranque rápido

```bash
# Docker (recomendado)
docker compose up

# O sin Docker
cd services/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd uis/backoffice && npm run dev   # :3001
```

Seeds útiles (API):

```bash
cd services/api
PYTHONPATH=. python seed_auth.py
PYTHONPATH=. python seed.py              # proveedores
PYTHONPATH=. python seed_inventory.py    # ingredientes (tras auth)
PYTHONPATH=. python seed_telemetry.py    # eventos telemetría
# Opcional histórico incidencias:
# python ../../scripts/seed_incidents.py ../../data/samples/backoffice/incidents-demo.csv
```

---

## 1. Reservas web → `/web-reservations`

| | |
|---|---|
| **Para qué** | Ver solicitudes de mesa enviadas desde la web pública `/reservas`. |
| **Cómo usar** | No se crean aquí. Abre **website `:3000/reservas`**, envía el formulario (o `POST /reservations` con el JSON de ejemplo). Luego refresca este módulo. |
| **Archivo** | `data/samples/backoffice/reserva-ejemplo.json` |
| **Nota** | Estado `received` = recibida, **no** mesa confirmada. Confirmación manual fuera del sistema. |

```bash
curl -sS -X POST http://localhost:8000/reservations \
  -H 'Content-Type: application/json' \
  -d @data/samples/backoffice/reserva-ejemplo.json
```

---

## 2. Candidaturas → `/careers`

| | |
|---|---|
| **Para qué** | Solicitudes de empleo desde `/trabaja-con-nosotros`. |
| **Cómo usar** | Rellena el formulario en la web pública; opcionalmente adjunta un CV (solo se guarda el nombre del fichero). |
| **Archivos** | `candidatura-ejemplo.json`, `cv-luis-herrera-demo.txt` |

```bash
TOKEN=$(curl -sS -X POST http://localhost:8000/auth/login \
  -d "username=admin@brasaland.com&password=TU_PASSWORD" | jq -r .access_token)
# Listar (JWT):
curl -sS http://localhost:8000/careers -H "Authorization: Bearer $TOKEN"
```

---

## 3. Recepción de RFP → `/rfp`

| | |
|---|---|
| **Para qué** | Subir PDF/MD de solicitud; el flujo LangGraph clasifica, reparte por departamento y (partes 2–3) genera/aprueba propuesta. |
| **Cómo usar** | 1) Sube un PDF. 2) Espera estados (`analizando` → `analisis_completo` o `descartado`). 3) Si aplica: generar borrador → aprobación HITL por depto. |
| **Archivos** | Ya en el repo: |
| | `rfp-requests/brasaland/brasaland-request-1.pdf` — RFP formal (aceptar, ~55–70k €) |
| | `rfp-requests/brasaland/brasaland-request-2.pdf` — catering informal (aceptar) |
| | `rfp-requests/brasaland/brasaland-request-3.pdf` — inválido (rechazar) |

SSE en vivo en la misma página (notificaciones de nuevos tickets).

---

## 4. Base de conocimiento → `/knowledge`

| | |
|---|---|
| **Para qué** | Preguntas en lenguaje natural sobre docs Brasaland (RAG / Qdrant). |
| **Cómo usar** | Escribe una pregunta y envía. Requiere Qdrant + colección indexada. |
| **Archivo** | `consulta-rag-ejemplos.txt` |
| **Nota** | Sin Qdrant/docs indexados la UI puede fallar o devolver vacío — no es “Failed to fetch” del login. |

---

## 5. Agente de soporte → `/agent`

| | |
|---|---|
| **Para qué** | Chat WebSocket del Manager agent (tokens en vivo, interrupt). |
| **Cómo usar** | Abre el módulo, escribe un mensaje, observa el stream; prueba **Interrumpir**. |
| **Archivo** | `chat-agente-ejemplos.txt` |
| **Nota** | El WS usa el origen directo `:8000` (no el proxy). En Codespaces el puerto 8000 debe ser **Public**. |

---

## 6. Costo y merma → `/reporting`

| | |
|---|---|
| **Para qué** | KPIs semanales de reporting (pipeline Prefect / tablas reporting). |
| **Cómo usar** | Abre el módulo; filtra/consulta según controles de la página. |
| **Datos** | Depende de haber corrido el pipeline / nightly; si está vacío, ejecuta el flow documentado en `data/pipelines/`. |

---

## 7. Telemetría → `/telemetry`

| | |
|---|---|
| **Para qué** | Ver eventos de uso del backoffice y reporte técnico. |
| **Cómo usar** | Navega otros módulos (genera eventos), luego abre Telemetría. O seed: `seed_telemetry.py`. |
| **Datos** | Se capturan solos al usar el panel (`track(...)`). |

---

## 8. Registrar incidencia → `/incidents/nueva`

| | |
|---|---|
| **Para qué** | Alta manual (sede / central / cliente). Estado inicial siempre **Abierta**. |
| **Cómo usar** | Completa título, descripción, categoría, origen y sede → Enviar. |
| **Archivo** | `incidencia-ejemplo.json` (referencia de campos; el alta normal es el formulario). |

---

## 9. Panel de incidencias → `/incidents`

| | |
|---|---|
| **Para qué** | Listar, filtrar y cambiar ciclo de vida (`open` → `in_progress` → `resolved` / `discarded`). |
| **Cómo usar** | Filtra por estado/origen/sede; usa las acciones de transición. |
| **CSV demo** | `incidents-demo.csv` + `scripts/seed_incidents.py` para cargar histórico. |

---

## 10. Resumen de incidencias → `/incidents/resumen`

| | |
|---|---|
| **Para qué** | Totales agregados (por estado, categoría, origen, sede). |
| **Cómo usar** | Solo lectura; se alimenta de las incidencias ya creadas. Cache ~30 s en API. |

---

## 11. Directorio de proveedores → `/proveedores`

| | |
|---|---|
| **Para qué** | CRUD de proveedores (tarifas, país, categorías, activo/suspendido). |
| **Cómo usar** | Tras `seed.py` ya hay datos. Alta con el formulario o JSON de ejemplo. |
| **Archivo** | `proveedor-ejemplo.json` |

---

## 12. Existencias de ingredientes → `/inventory/products`

| | |
|---|---|
| **Para qué** | Stock calculado en tiempo real + alertas de stock bajo. |
| **Cómo usar** | Ejecuta `seed_inventory.py`, luego abre el módulo. |

---

## 13. Entrada de ingredientes → `/inventory/orders/inbound`

| | |
|---|---|
| **Para qué** | Registrar entrega de proveedor (local 1–14, cantidad, coste opcional). |
| **Cómo usar** | Elige ingrediente, sede, cantidad, nombre proveedor → Enviar. Sube el stock. |

---

## 14. Salida / merma → `/inventory/orders/outbound`

| | |
|---|---|
| **Para qué** | Consumo o merma; muestra stock antes de confirmar. |
| **Cómo usar** | Igual que entrada pero resta stock. No envíes más de lo disponible. |

---

## 15. Historial de inventario → `/inventory/orders`

| | |
|---|---|
| **Para qué** | Listado de órdenes in/out con ingrediente y autor. |
| **Cómo usar** | Solo consulta tras haber hecho entradas/salidas. |

---

## 16. Mi cuenta → `/account/profile`

| | |
|---|---|
| **Para qué** | Ver/editar nombre y contacto del usuario JWT; cambio de contraseña en subruta. |
| **Cómo usar** | Edita campos y guarda. `/account/change-password` para la clave. |

---

## Orden recomendado para una demo

1. Login → confirmar `/api-backend`
2. Proveedores + Existencias (seeds)
3. Entrada → Salida → Historial
4. Registrar incidencia → Panel → Resumen
5. Website: reserva + candidatura → módulos web
6. RFP: subir `brasaland-request-1.pdf` (y opcional 2/3)
7. Knowledge / Agente (si Qdrant + LLM configurados)
8. Telemetría / Reporting
