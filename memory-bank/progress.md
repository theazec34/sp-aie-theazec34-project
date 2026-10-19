# Progress — Brasaland Digital

## Estado (2026-10-19)
- **`main`:** PRs **#1–#44** (RFP Parte 2 #44 mergeado).
- **Hito en curso:** **Hito 9 Parte 3 — aprobación HITL + documento final** (`feature/rfp-approval-completion`).
- **Moneda de producto RFP/propuestas:** **euros (€)**.
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## RFP Parte 3 (hito actual)
- Interrupt + checkpointer SQLite por departamento (`rfp-{ticket_id}:{dept}`)
- Aprobaciones paralelas no bloqueantes; resume explícito
- Arbitraje fijo BRIEFING §7 (no LLM)
- Documento final → `terminado`; CEO si > 50.000 €/año
- API: `/approvals/start`, `/approvals/{dept}`, `/final-document`
- Tests: `test_rfp_approval.py` + E2E `scripts/run_rfp_e2e_approval.py`
- Docs: `docs/rfp/rfp-approval-completion-part3.md`

## RFP Partes 1–2
- #42 intake · #44 generación/evaluación

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#43 |
| RFP generación Parte 2 | #44 |
| RFP aprobación Parte 3 + € | este PR |
