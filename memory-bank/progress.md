# Progress — Brasaland Digital

## Estado (2026-10-20)
- **`main`:** PRs **#1–#47** (WebSocket chat #47 mergeado).
- **Hito en curso:** **OWASP Top 10 + IA segura** (`cursor/owasp-top10-audit-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Seguridad / OWASP (hito actual)
- Informe OWASP: `docs/security/owasp-top10-audit.md`
- Informe NIST AI-secure (Ley 1581 + FIPA): `docs/security/nist-ai-secure-practices.md`
- Hardening: `scripts/hardening/` + compose (Redis/Qdrant internos, Flower loopback)
- Fixes críticos: JWT en `/api/incidents`, seed_auth sin password en código, proveedor `confirm`+admin, probe Brasa Points
- Tests: `test_incidents.py`, `test_supplier_irreversible.py`, guardrail Brasa Points

## Tiempo real (en main)
- #46 SSE RFP · #47 WebSocket agent chat

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#46 |
| WebSocket agent chat | #47 |
| OWASP + IA segura | #48 |
