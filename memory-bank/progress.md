# Progress — Brasaland Digital

## Estado (2026-10-19)
- **`main`:** PRs **#1–#42** (RFP intake #42 mergeado; Agent Memory #40; Guardrails en main).
- **Hito en curso:** limpieza de cohesión + español (`cursor/project-cleanup-es-c620`).
- **Siguiente:** Hito 9 Parte 2 (generación/evaluación de secciones) tras merge de limpieza.
- **Fuera de alcance:** `hito-3` / `3.5`.
- **Estabilidad:** `AGENTS.md` (base main, un hito→PR→merge, `uv add`, RAG≠memoria, **español UI**).

## Limpieza / cohesión (este PR)
- Fuente única de departamentos RFP (`data/pipelines/rfp_intake/departments_ref.py`)
- Bug mapeo clasificador → DB (`confidence`/`notes` → `classifier_*`)
- Estado terminal `fallido` si el pipeline rompe (deja de quedar en `analizando`)
- Docker: copia `services/rfp` + `mcps` al image de la API
- UI/API en español (nav, RFP, inventario, reporting, knowledge, agente)
- Memory bank / README / `apps/README.es.md` alineados

## RFP Intake Parte 1 (#42)
- Grafo `data/pipelines/rfp_intake/` · SQLModel tickets · backoffice `/rfp`
- Semillas `rfp-requests/brasaland/` · CLI `scripts/run_rfp_intake.py`
- Docs: `docs/rfp/rfp-intake-part1.md`

## Agent Guardrails (Hito 8 Parte 2)
- `services/agent/guardrails/` · tests `test_agent_guardrails.py`
- Docs: `docs/agent/agent-guardrails.md`

## Agent Memory (#40)
- Episódica `brasaland_agent_memory` + confirmación explícita

## MCP OAuth tools (#39)
- `mcps/brasaland_tools/` + agente vía MCP

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#38 |
| MCP OAuth tools | #39 |
| Agent Memory | #40 |
| Agent Guardrails | #41 (si aplica) / main |
| RFP intake Parte 1 | **#42** |
| Limpieza ES + cohesión | **#43** |
