# RFP — Parte 2: generación y evaluación de borradores

Parte 1 clasifica la RFP y deja un **handoff** (`ticket_id` + synthesizer / `key_aspects`).
Parte 2 **no re-parsea el PDF**: convierte ese handoff en borradores de propuesta económica
por departamento, los evalúa en paralelo y, si fallan, cicla generador↔evaluador hasta un
límite.

## Qué pide el README (implicación)

| Pedido | Implicación en el monorepo |
|--------|----------------------------|
| Consumir handoff Parte 1 | `POST /rfp/tickets/{id}/generate` lee SQLModel; no MarkItDown otra vez |
| Generador por departamento | `data/pipelines/rfp_intake/generators.py` (marketing, operaciones, procurement, training) |
| Evaluadores en paralelo | Legibilidad + pertinencia + cumplimiento BRIEFING §5 (`evaluators.py`) |
| Ciclo + límite | `MAX_GENERATOR_ITERATIONS=3`; si se agota → `needs_human_review` |
| Persistencia Postgres | `draft_content`, `evaluation_results_json`, flags en `rfp_department_section` |
| Sin segunda API | Mismo FastAPI `services/api` + runner `services/rfp` |
| BRIEFING, no genérico | Departamentos y reglas de `docs/rfp/brasaland-BRIEFING.es.md` |

## Estados del ticket (Parte 2)

`analisis_completo` → `generando_borrador` → `en_evaluacion` →  
`borrador_listo` (todas las secciones pasan) **o** `needs_human_review` (límite agotado en alguna).

No se usan aún `esperando_aprobacion` / `terminado` (Parte 3).

## EvaluationResult (por sección)

```json
{
  "section_id": "operaciones",
  "department_id": "operaciones",
  "readability": { "pass": true, "score": 12.3, "details": "..." },
  "relevance": { "pass": true, "missing_aspects": [] },
  "compliance": { "pass": false, "rule_ids": ["setup-min-10-days"], "violations": ["..."] },
  "overall_pass": false,
  "feedback_for_generator": "Corrige cumplimiento BRIEFING: setup-min-10-days."
}
```

## API / UI

- `POST /rfp/tickets/{id}/generate` → **202** + `generando_borrador`
- Poll `GET /rfp/tickets/{id}`
- Backoffice `/rfp` → botón «Generar borradores (Parte 2)»

## Pruebas

```bash
uv run pytest tests/pipelines/test_rfp_generation.py tests/pipelines/test_rfp_intake.py -q
```

## Decisiones de diseño

1. **Estado que ven los evaluadores:** solo la sección (borrador) + metadatos + `key_aspects` del handoff; no el PDF completo.
2. **Escritura concurrente:** cada sección produce su propio `EvaluationResult` en memoria; el runner persiste al final (sin carrera en DB).
3. **`needs_human_review` para Sales:** badge en UI + `section_status` + mensaje de borrador provisional.
4. **Feedback concreto:** incluye `rule_ids` / `missing_aspects`, no frases vagas.
