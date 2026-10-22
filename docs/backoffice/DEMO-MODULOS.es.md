# Demo rápida de módulos (backoffice `:3001`)

## Reservas / Candidaturas
Solo llegan si se envían desde la web (`:3000/reservas`, `/trabaja-con-nosotros`).  
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

**Si timeout con API key OK:** suele ser Qdrant sin indexar o FastEmbed bajando el modelo.
```bash
# Indexar corpus (1–3 min)
docker compose exec backend python -c "from data.process.rag import setup; print(setup())"
# Probar LLM 4Geeks (debe imprimir una frase)
docker compose exec backend python - <<'PY'
import os
from openai import OpenAI
c = OpenAI(base_url=os.environ["GENERATION_BASE_URL"], api_key=os.environ["GENERATION_API_KEY"], timeout=30)
r = c.chat.completions.create(
    model=os.environ["GENERATION_MODEL_ID"],
    messages=[{"role":"user","content":"Di solo: hola brasaland"}],
)
print(r.choices[0].message.content)
PY
```
En la UI: botón **Reindexar manuales**.

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
