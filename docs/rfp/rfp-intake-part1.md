# RFP Intake — Parte 1 (Hito 9)

Flujo agéntico de recepción y enrutamiento de RFPs para Marketing (Camila Ospina).

## Layout

| Pieza | Ubicación |
|-------|-----------|
| Grafo LangGraph | `data/pipelines/rfp_intake/` |
| Persistencia SQLModel | `services/api/app/rfp/` (PostgreSQL/Supabase; SQLite fallback) |
| Runner async | `services/rfp/runner.py` |
| HTTP | `POST/GET /rfp/tickets` en el API existente |
| UI | `uis/backoffice` → `/rfp` |
| CLI | `scripts/run_rfp_intake.py` |
| Semillas | `rfp-requests/brasaland/` |
| BRIEFING | `docs/rfp/brasaland-BRIEFING.es.md` |

**No** se crea un segundo servicio HTTP. TinyDB **no** es fuente de verdad de tickets.

## Estados (Parte 1)

`analizando` → `analisis_completo` | `descartado` | `fallido`

- `fallido`: excepción a mitad de pipeline (mensaje en español en `error_message`; detalle técnico solo en logs).
- `esperando_aprobacion` no se usa en Parte 1.

## Idioma

UI, `detail` HTTP y resúmenes del synthesizer en **español** (`AGENTS.md` ley 9). Los `department_id` y códigos de estado se mantienen como en el BRIEFING.

## Pipeline

1. **convert** — PDF → Markdown (`MarkItDown`) + métricas (`py-readability-metrics`: Flesch-Kincaid, Gunning Fog)
2. **classify** — ¿Es RFP B2B? Si no → `descartado`
3. **orchestrate** — workstreams por `department_id` del BRIEFING
4. **workers** — `marketing` / `operaciones` / `procurement` / `training` (solo los que apliquen)
5. **synthesize** — brief para Sales: qué pedir a quién + `key_aspects`

## Async upload

`POST /rfp/tickets` guarda el PDF en `data/raw/`, crea ticket `analizando`, responde **202** y encola el grafo en un thread pool. La UI hace poll a `GET /rfp/tickets/{id}`.

## Handoff Parte 2

Cuando `status=analisis_completo`:

- `rfp_ticket.handoff_ready = true`
- `rfp_ticket.synthesizer_payload_json` = payload del synthesizer
- filas `rfp_department_section` con `key_aspects`

Contrato: `{ ticket_id, synthesizer_payload, department_sections }` — sin re-parsear el PDF.

## Pruebas

```bash
uv run pytest tests/pipelines/test_rfp_intake.py -q
uv run python scripts/run_rfp_intake.py rfp-requests/brasaland/brasaland-request-1.pdf
```

Semillas BRIEFING:

1. `brasaland-request-1` — Sunset Bay (formal, 4 deptos) → aceptar
2. `brasaland-request-2` — Andes Tech (informal, sin training) → aceptar
3. `brasaland-request-3` — franquicia → `descartado`

## Decisiones de diseño

### Departamento no listado en el BRIEFING

No se inventa un quinto departamento. `normalize_departments` / `resolve_unknown_department`
(en `data/pipelines/rfp_intake/departments_ref.py`, reexportado por el API) mapean aliases
(`ops`→`operaciones`, etc.) o descartan ids desconocidos; marketing siempre entra en el loop.

### Qué reciben los workers

Metadatos compartidos + Markdown completo (extractos vía regex por depto). Cifras faltantes → `open_questions`; **nunca** se inventan volúmenes/precios.

### Criterio “no es RFP”

Franquicia / consulta general sin alcance **y** sin fecha límite → rechazo explícito (no fallo silencioso). LOIs informales con cliente + servicio + (alcance o deadline) se aceptan (evitar falsos negativos).

### Contradicciones entre workers

Parte 1 no auto-resuelve: `merge_worker_conflicts` añade notas a `open_questions` para Camila.

### Dónde corre el job async

`ThreadPoolExecutor` en el API (`POST` responde 202 y encola). Si falla a mitad →
estado `fallido` + `error_message` legible (SoT = fila `rfp_ticket`). Celery/Prefect
quedan disponibles para Parte 2+ si el volumen lo exige.
