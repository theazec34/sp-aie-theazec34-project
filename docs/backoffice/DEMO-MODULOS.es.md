# Demo rápida de módulos (backoffice `:3001`)

## Seed demo multi-sede (preguntas del agente)
Al arrancar el backend se ejecuta `seed_demo_ops.py` (además de suppliers/inventory).
Crea proveedores por sede (`notes` con `branch=miami_doral`…), reservas **hoy/mañana**,
candidaturas, movimientos de inventario (kg) e incidencias.

```bash
# Re-sembrar a mano (idempotente; fuerza con SEED_DEMO_FORCE=1)
docker compose exec -T backend python seed_demo_ops.py
# o:
docker compose exec -T backend sh -c 'SEED_DEMO_FORCE=1 python seed_demo_ops.py'
```

Preguntas útiles al **Agente soporte**:
- ¿Cuál es el proveedor con la tarifa más alta en €?
- ¿Qué proveedor nos ha enviado más kg?
- ¿Qué stock tenemos ahora?
- ¿Estado de la incidencia en Miami Doral?

Reservas/candidaturas sembradas también aparecen en **Reservas web** / **Candidaturas**.

## Reservas / Candidaturas
También llegan si se envían desde la web (`:3000/reservas`, `/trabaja-con-nosotros`).  
`reservas@brasaland.com` es un `mailto:` — **no** hay bandeja de correo en el panel.

## Recepción de RFP
Pipeline IA: subes un PDF de petición de propuesta → clasifica → borradores por depto → aprobación humana → documento final en **€**.

**PDFs de ejemplo (ya en el repo):**
```
rfp-requests/brasaland/brasaland-request-1.pdf   # formal, aceptar
rfp-requests/brasaland/brasaland-request-2.pdf   # catering informal
rfp-requests/brasaland/brasaland-request-3.pdf   # inválido → descartar
```
En Codespaces: descarga el PDF desde el explorador de archivos → súbelo en **Recepción RFP** → Crear ticket.  
SSE «Desconectado» = refresca con puerto **8000 Public**.

## BrasAI (antes «Base de conocimiento») + Agente
Menú: **BrasAI**. No usan `LLM_*` a pelo: el runtime lee `GENERATION_*`.  
Alias: `LLM_BASE_URL` → `GENERATION_BASE_URL`, `LLM_MODEL` → `GENERATION_MODEL_ID`, `LLM_API_KEY` → `GENERATION_API_KEY`.  
Si el LLM falla, BrasAI cae a modo **grounded** (texto de los manuales) en vez de quedarse colgado.

**Si timeout / FastEmbed no baja de HuggingFace** (`Temporary failure in name resolution`):
```bash
# En .env (o ya forzado en compose): embeddings offline
EMBEDDING_PROVIDER=hash

docker compose up -d --force-recreate backend
docker compose exec backend python -c "from data.process.rag import setup; print(setup())"
```
Costo y merma «No se pudo conectar …-8000…»: en login usa **`/api-backend`** (borra la URL …-8000 del campo API) y recarga.

En `.env` (raíz), ejemplo 4Geeks:
```bash
GENERATION_PROVIDER=openai
GENERATION_BASE_URL=https://llm.4geeks.ai/v1
GENERATION_MODEL_ID=madrid-spain/opnerouter/openai/gpt-6-luna
GENERATION_API_KEY=tu-clave   # no la pegues en el chat
EMBEDDING_PROVIDER=fastembed
```
Luego: `docker compose up -d --force-recreate backend`

El **agente no simula empleados**: es un chat IA para el encargado. «En vivo» = WebSocket OK; sin respuesta = falta clave/modelo o puerto 8000 no Public.

## Costo y merma
KPIs semanales (compra, merma, quiebres). Vacío hasta correr el pipeline:
1. Sembrar telemetría: `docker compose exec backend python seed_telemetry.py`
2. En la UI: **Recalcular semana** (o `POST /reporting/pipeline-runs` con JWT)
3. Puerto 8000 Public + «Usar auto-detectada» en login

## Telemetría / Reporte técnico
Radar de ingeniería (page views, errores, login, latencia). No es dashboard de negocio.  
Tras `seed_telemetry.py` y reinicio, pulsa **Actualizar** (rango = últimos días UTC).

## Proveedores e inventario
- **Entrada inventario** = compra a proveedor (aumenta stock).
- **Salida inventario** = consumo / merma (baja stock).
- **Todas las tarifas en EUR (€)**; al sembrar se convierte COP÷4300 y USD×0.92.
- Re-sembrar: `docker compose exec backend python seed.py --force`
- RFP necesita `markitdown` en la imagen backend (`docker compose up -d --build backend`).

## Cambiar contraseña
Va en **Mi cuenta → Cambiar contraseña** (ya no en el menú lateral).
