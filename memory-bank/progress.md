# Progress — Brasaland Digital

## Estado (2026-10-19)
- **`main`:** PRs **#1–#43** (limpieza ES #43; RFP Parte 1 #42).
- **Hito en curso:** **Hito 9 Parte 2 — generación/evaluación RFP** (`feature/rfp-response-generation`).
- **Fuera de alcance:** `hito-3` / `3.5`.
- **Estabilidad:** `AGENTS.md` (base main, español UI, RAG≠memoria).

## RFP Parte 2 (hito actual)
- Consume handoff Parte 1 (`ticket_id` + synthesizer/`key_aspects`) — sin re-parsear PDF
- Generadores por depto + evaluadores paralelos (legibilidad, pertinencia, cumplimiento BRIEFING §5)
- Ciclo generador↔evaluador con límite → `needs_human_review` o `borrador_listo`
- API: `POST /rfp/tickets/{id}/generate` (202)
- Persistencia: `draft_content`, `evaluation_results_json` en SQLModel
- Docs: `docs/rfp/rfp-response-generation-part2.md`
- Tests: `tests/pipelines/test_rfp_generation.py`

## RFP Intake Parte 1 (#42)
- Grafo `rfp_intake` · tickets · backoffice `/rfp`

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#41 |
| RFP intake Parte 1 | #42 |
| Limpieza ES + cohesión | #43 |
| RFP generación Parte 2 | este PR |
