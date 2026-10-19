# RFP — Parte 3: aprobación humana y cierre del documento

## Qué pide el README

Tras los borradores autoevaluados (Parte 2), cada departamento debe **aprobar en humano**
su sección. El flujo:

1. Pausa con `interrupt` + `checkpointer` (SQLite en `data/rfp_checkpoints/`).
2. La pausa de un depto **no bloquea** a los demás (`thread_id = rfp-{ticket_id}:{dept}`).
3. Árbitro fijo (BRIEFING §7), no consenso LLM.
4. Cuando todos firman (+ CEO si > 50.000 €/año) → documento final y `terminado`.

## Moneda

Toda la propuesta económica usa **euros (€)**. Regla de cumplimiento: `price-eur`.
Umbral CEO: **50.000 €/año**.

## Estados

`borrador_listo` / `needs_human_review` → `esperando_aprobacion` → `terminado`

## API

| Método | Ruta | Rol |
|--------|------|-----|
| POST | `/rfp/tickets/{id}/approvals/start` | Arranca HITL (202) |
| POST | `/rfp/tickets/{id}/approvals/{department_id}` | `approve` / `reject` / `request_changes` |
| GET | `/rfp/tickets/{id}/final-document` | Documento consolidado |

`department_id=ceo` para Mariana Restrepo cuando aplica el umbral.

## Decisiones de diseño

1. **Rechazo:** vuelve a interrupt del mismo departamento (límite `MAX_APPROVAL_ITERATIONS`); no reinicia Parte 1.
2. **UI mínima:** borrador excerpt + aspectos clave + botones Aprobar / Pedir cambios / Rechazar.
3. **Conflictos:** detectados en estado estructurado (`arbitration.py`: setup-sla-breach, cost-vs-feasibility, ceo-threshold).

## Pruebas

```bash
uv run pytest tests/pipelines/test_rfp_approval.py tests/pipelines/test_rfp_generation.py -q
uv run python scripts/run_rfp_e2e_approval.py
```
