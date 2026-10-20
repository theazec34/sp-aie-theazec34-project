# Progress — Brasaland Digital

## Estado (2026-10-20)
- **`main`:** PRs **#1–#49** (NIST #49 mergeado).
- **Hito en curso:** auditoría de polish UI (marca / bugs / UX) — `cursor/ui-polish-audit-713f`.
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## UI polish audit (2026-10-20)
Auditoría solo-lectura de `uis/website` + `uis/backoffice` (globals, layout, home, login, agent, rfp, knowledge).

### Hallazgos clave
- **Website tokens:** `--brasa` `#c8380a`, `--carbon` `#1a1008`, `--crema` `#fdf6ec`, Playfair + DM Sans — crema dominante (anti-patrón cream/terracotta); brand débil en H1 del hero.
- **Backoffice tokens:** SaaS slate/cyan (`--bo-accent` `#0e7490`, sidebar `#0f172a`) — desconectado de brasa/carbón.
- **Bug crítico:** `skipAuth: true` en POST/PATCH incidencias tras OWASP JWT → 401 (`incidents/page.tsx`, `incidents/nueva/page.tsx`); README backoffice obsoleto.
- **Español:** faltan tildes en hero/formulario (`Sudamerica`, `aplicacion`, `anos`…); agent/RFP con inglés de producto (`Manager support agent`, `Parte 2/3`).
- **Páginas crudas:** RFP botones sin `bo-btn`; knowledge usa `.bo-input` inexistente; agent `location_id` crudo.

### Cómo arrancar
`cp .env.example .env && docker compose up --build` → :3000 / :3001 / :8000/docs

## NIST security practices (en main · #49)
- Informe CSF 6 funciones: `docs/security/nist-csf-ai-report.md`
- Rate limit LLM + decision log del agente

## Seguridad / OWASP (en main)
- #48 — OWASP Top 10 + hardening + fixes críticos

## Tiempo real (en main)
- #46 SSE · #47 WebSocket

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#47 |
| OWASP + IA segura | #48 |
| NIST CSF practices | #49 |
| UI polish audit | este branch |
