# Project Brief — Brasaland Digital

## Negocio
Restaurante Brasaland: sala, carta/marketing, logística/proveedores, domicilio e incidencias postventa.

## Entidades TS (`Brasaland.md` → `src/`)
- `EncargoProveedor`
- `PlatoCarta`
- `ReservaMesa`
- `PedidoDomicilio`

## Producto en main
Plataforma digital con:
1. Web pública Next (`uis/website`)
2. Backoffice ops Next (`uis/backoffice`) — telemetría, reporting, knowledge
3. API FastAPI (`services/api`) — auth JWT, proveedores, incidencias, inventario, telemetry, reporting, knowledge, tasks, agent
4. Docker Compose + informes de performance/caching
5. Pipeline Prefect + nightly export (`job_runs`)
6. ML: sentimiento WeLoveReviews + forecast/eval de ventas
7. RAG: base de conocimiento Qdrant (`brasaland_knowledge`) + `/knowledge`
8. Celery/Redis (DEV-55): analyze async + Flower
9. LangGraph agent (Part 1–2): grafo explícito sobre RAG + tools + `/agent/query`
10. MCP Server OAuth (`mcps/brasaland_tools`): incidents + inventory; agente como cliente MCP
11. Agent Memory episódica (`brasaland_agent_memory`) con confirmación explícita del usuario
12. Agent Guardrails / harness de seguridad (anti-jailbreak, alcance, aislamiento RAG)
13. RFP intake Parte 1: tickets PDF → LangGraph `rfp_intake` → key_aspects por departamento (SQLModel)
14. Idioma de producto: español en UI y mensajes al operador (`AGENTS.md` ley 9)
15. RFP Parte 2: generadores + evaluadores paralelos + ciclo con `needs_human_review`
16. RFP Parte 3: HITL por departamento (interrupt/checkpointer) + documento final; moneda €
17. SSE: notificaciones push de tickets RFP (y alerta opcional de caída de ventas) al backoffice
18. WebSocket: chat en vivo del Manager support agent (tokens + abort + rehidratación de sesión)
19. Seguridad: auditoría OWASP Top 10 + prácticas IA (Ley 1581 / FIPA) con fixes críticos

## Fuentes de verdad
- Mapa operativo: **`PROJECT.md`**
- Negocio restaurante: `Brasaland.md`
- Incidencias CSV / centralizadas / inventario: CONTEXT*.md correspondientes
- RAG: `docs/rag/CONTEXT-brasaland.es.md`

## Fuera de alcance en main
- Talent Pipeline Tracker (`hito-3` / rama `3.5`) — no mergeado
- Brasaland Agent experimental histórico — sustituido por `services/agent` LangGraph
