# Progress — Brasaland Digital

## Estado (2026-10-20)
- **`main`:** PRs **#1–#48** (OWASP #48 mergeado).
- **Hito en curso:** **NIST CSF — prácticas seguras IA** (`cursor/nist-security-practices-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## NIST security practices (hito actual)
- Informe CSF 6 funciones: `docs/security/nist-csf-ai-report.md` (Ley 1581 + FIPA)
- Rate limit: `POST /agent/query` + `POST /knowledge/query` → 429 (`app/rate_limit.py`)
- Decision log: `agent/decision_log.py` + `GET /agent/decisions/recent`
- Prompt injection + HITL irreversibles: heredados de #48 / tests existentes
- Tests: `test_agent_rate_limit.py`, `test_agent_decision_log.py`

## Seguridad / OWASP (en main)
- #48 — OWASP Top 10 + hardening + fixes críticos

## Tiempo real (en main)
- #46 SSE · #47 WebSocket

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#47 |
| OWASP + IA segura | #48 |
| NIST CSF practices | este PR |
