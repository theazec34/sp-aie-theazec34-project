# Technical Context — Brasaland Digital (actualizado 2026-10-19)

## Runtime
- **Website** `uis/website` — Next.js 16, puerto **3000**
- **Backoffice** `uis/backoffice` — Next.js 16, puerto **3001**
- **API** `services/api` — FastAPI/uvicorn, puerto **8000** (`/docs`)
- **Redis / Celery / Flower** — broker `:6379`, Flower `:5555` (DEV-55)
- **Qdrant** — `:6333` (RAG)
- **Docker:** `docker compose up` (ver `DOCKER.md`); `llm-proxy` (host :18080) para egress LLM en Codespaces; DNS/extra_hosts en backend/worker
- **TS Hito 2:** `src/` — `npm run typecheck` / `npm run demo`
- **E2E:** Playwright → website `:3000` (`npm run test:e2e`)
- **API tests:** `cd services/api && uv run pytest`

## Persistencia
- TinyDB: auth, profiles, suppliers, incidents (gitignored bajo `services/api/data/`)
- SQLModel inventario: `DATABASE_URL` (Supabase) o SQLite fallback

## API (grupos)
- Auth/users/profiles · Suppliers · Incidents (`/api/incidents`, analyze/export) · Inventory (`/inventory/*`)
- Cache TTL: summary 30s, suppliers 60s (`app/cache.py`) + middleware `api.timing`

## Frontends
- Website: carta + galería lazy + formulario lazy
- Backoffice: JWT, proveedores, incidencias, inventario (`useAsyncResource`, `AuthenticatedShell`)
- `uis/web`: analizador CSV montado en API `/`

## Docs canónicos
- `PROJECT.md` — mapa completo
- `README.md`, `DOCKER.md`, `CACHING_REPORT.md`, `AUDIT.md`, `REPORT.md`, `TESTING.md`
- Contextos: `Brasaland.md`, `CONTEXT-brasaland.es.md`, `CONTEXT-incidents-centralized.es.md`, `05-backend-inventory-orm/`
- Telemetría (diseño): `docs/telemetry/telemetry-plan.md`, `event-schemas.json`

## Telemetría
- Diseño: `docs/telemetry/telemetry-plan.md`, `event-schemas.json`
- Captura: `uis/backoffice/src/services/telemetry.ts` (`track`)
- Almacenamiento: `POST /telemetry/events` → `telemetry_events` (bulk); SQL `services/api/sql/telemetry_events.sql`
- Reporte técnico: `services/telemetry/analysis.py` + `GET /telemetry/report` (cache 60s) + UI `/telemetry`
- Docs: `docs/telemetry/CAPTURE.md`, `STORAGE.md`, `REPORT.md`

## Pipeline de negocio
- Diseño: `data/pipelines/PIPELINE_DESIGN.md`
- Flow + subflows: `data/pipelines/pipeline.py`
- Destino: `reporting.weekly_location_performance`
- API: `services/reporting/router.py` → `/reporting/*`
- Dashboard: backoffice `/reporting`
- Tests: `tests/pipelines/test_pipeline.py`

## Orquestación nocturna (DEV-53)
- Script: `scripts/nightly_export.py` (proceso independiente, no FastAPI)
- Estado: `job_runs` (`services/job_runner/`, SQL `services/api/sql/job_runs.sql`)
- CSV backup: `data/raw/telemetry_YYYY-MM-DD.csv` (auditoría; pipeline lee DB)
- Cron ejemplo: `scripts/crontab.example` — `0 2 * * *` UTC
- Tests: `tests/scripts/test_nightly_export.py`

## ML — WeLoveReviews (sentimiento)
- Notebook: `src/explore.ipynb` · Script: `src/app.py` · Helpers: `src/sentiment_analysis.py`
- Modelo HF: `nlptown/bert-base-multilingual-uncased-sentiment` (carga única, sin pesos en git)
- Datos: `data/raw/reviews.csv` → `data/processed/reviews_with_sentiment.csv`
- Deps: `requirements.txt` (raíz, hito ML)

## ML — predicción de ventas Brasaland
- CONTEXT: `CONTEXT-brasaland.es.md`
- Datos: `data/raw/brasaland_sales.csv`
- Train: `scripts/train_sales_forecast.py` → `models/brasaland_sales_forecast.joblib`
- Paquete: `scripts/sales_forecast/` (data + metrics)
- Salidas train: `data/forecast/` (report, metrics, prediction_band)
- Eval técnica (hito posterior): `scripts/evaluate_revenue_model.py` → `data/eval/`
- Tests: `tests/pipelines/test_sales_forecast_split.py`, `test_temporal_cv.py`
- Deps: `uv` (`pyproject.toml`)


## Celery / Redis (DEV-55)
- App: `services/celery_app.py` · tasks: `services/tasks/`
- Broker/backend: `REDIS_URL` (Compose: `redis://redis:6379/0`)
- Analyze async: `POST /api/v1/incidents/analyze` → 202 `{task_id}`
- Status: `GET /tasks/{task_id}` · DLQ: `celery_dead_letters`
- Flower: `:5555` · worker proceso independiente
- Compose: Redis `protected-mode no` + healthcheck (sin ports host); worker/flower esperan healthy
- Docs: `docs/async-tasks/DEV-55.md`

## RFP Intake (Hito 9 · Parte 1)
- Grafo: `data/pipelines/rfp_intake/` (MarkItDown → classifier → orchestrator-worker-synthesizer)
- Persistencia: SQLModel `rfp_ticket` / `rfp_metadata` / `rfp_department_section` (Postgres/Supabase)
- API: `POST /rfp/tickets` (202 async), `GET /rfp/tickets`, `GET /rfp/tickets/{id}`
- Runner: `services/rfp/runner.py` (ThreadPoolExecutor)
- UI: backoffice `/rfp`
- Semillas: `rfp-requests/brasaland/` · CLI: `scripts/run_rfp_intake.py`
- Docs: `docs/rfp/rfp-intake-part1.md`, `docs/rfp/brasaland-BRIEFING.es.md`
- Tests: `tests/pipelines/test_rfp_intake.py`
- Deps: `markitdown`, `py-readability-metrics`, `reportlab` (fixtures)

## RFP Response Generation (Hito 9 · Parte 2)
- Grafo/ciclo: `generation_graph.py` + `generators.py` + `evaluators.py` + `guidelines.py`
- Entrada: handoff Parte 1 (no re-parsea PDF)
- API: `POST /rfp/tickets/{id}/generate` → 202
- Estados: `generando_borrador` → `en_evaluacion` → `borrador_listo` | `needs_human_review`
- EvaluationResult: legibilidad / pertinencia / cumplimiento (BRIEFING §5, moneda €)
- Docs: `docs/rfp/rfp-response-generation-part2.md`
- Tests: `tests/pipelines/test_rfp_generation.py`
- CLI: `scripts/run_rfp_generation.py`

## RFP Approval Completion (Hito 9 · Parte 3)
- `approval_graph.py` (interrupt + SqliteSaver) · `arbitration.py` · `final_document.py`
- thread_id: `rfp-{ticket_id}:{department_id}` (paralelo no bloqueante)
- API: approvals/start, approvals/{dept}, final-document
- Estados: `esperando_aprobacion` → `terminado`
- Checkpoints: `data/rfp_checkpoints/rfp_approval.sqlite` (gitignore)
- Deps: `langgraph-checkpoint-sqlite`
- Tests: `test_rfp_approval.py` · E2E `scripts/run_rfp_e2e_approval.py`
- Docs: `docs/rfp/rfp-approval-completion-part3.md`
- Moneda: **EUR (€)** · umbral CEO 50.000 €/año

## SSE — notificaciones RFP en tiempo real
- Hub: `services/api/app/rfp/sse_hub.py` (fan-out in-process + replay ~100)
- API: `GET /rfp/events/stream` (JWT, `text/event-stream`)
- Eventos: `rfp_ticket_created` (al `POST /rfp/tickets`); opcional `sales_drop_alert`
- UI: `uis/backoffice/src/lib/rfpSse.ts` — `fetch` + ReadableStream (no EventSource bare)
- Reconexión: backoff + `Last-Event-ID` + refetch lista + dedupe `ticket_id`
- Docs: `docs/rfp/sse-notifications.md`
- Tests: `services/api/tests/test_rfp_sse.py`
- Sin modelos/agentes en esta capa

## Seguridad — OWASP Top 10 + IA segura
- Informes: `docs/security/owasp-top10-audit.md`, `nist-ai-secure-practices.md` (Ley 1581 + FIPA)
- Hardening: `scripts/hardening/{00-baseline,10-apply-host,20-verify}.sh`
- Compose: Redis/Qdrant sin ports host; Flower `127.0.0.1:5555` + basic auth
- `/api/incidents` JWT; proveedores status/delete = admin + `confirm`
- Seed admin: `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` (env only)
- BRIEFING: `docs/security/brasaland-BRIEFING-ai-secure.es.md`

## NIST CSF — prácticas seguras IA
- Informe 6 funciones: `docs/security/nist-csf-ai-report.md`
- Rate limit LLM: `app/rate_limit.py` en `/agent/query` y `/knowledge/query` (429)
- Decision audit: `services/agent/decision_log.py` + `GET /agent/decisions/recent`
- Env: `AGENT_RATE_LIMIT_*`, `KNOWLEDGE_RATE_LIMIT_*`
- Tests: `services/api/tests/test_agent_rate_limit.py`, `tests/pipelines/test_agent_decision_log.py`

## WebSocket — chat Manager support agent (tiempo real Parte 2)
- Paquete: `services/agent/chat/` (pubsub, sessions, streamer, ws)
- Endpoint: `WS /agent/chat/ws?token=&session_id=&location_id=`
- ChatSession BRIEFING: `session_id`, `agent_id=manager_support`, `user_id`, `location_id`, status
- Pub/Sub canal `chat.<session_id>`; abort ≠ LangGraph HITL interrupt()
- UI: backoffice `/agent` + `lib/agentChatWs.ts` (backoff + rehidratación)
- Docs: `docs/realtime/websocket-chat.md`, `docs/realtime/brasaland-BRIEFING.es-2-2.md`
- Tests: `services/api/tests/test_agent_chat_ws.py`
- No rediseña el grafo: reutiliza `run_agent`

## Agent Guardrails (Hito 8 · Parte 2)
- Paquete: `services/agent/guardrails/`
- Capas: system prompt seguro, input/output guards, aislamiento RAG/tool, observabilidad
- API: `GET /agent/guardrails/summary`
- Docs: `docs/agent/agent-guardrails.md`
- Evals: `tests/pipelines/test_agent_guardrails.py`

## Agent Memory (Hito 8 · Parte 1)
- Paquete: `services/agent/memory/` — namespace `brasaland_agent_memory` (file/Redis)
- Nunca escribe en Qdrant `brasaland_knowledge` / `*_knowledge`
- Flujo: self-eval → propuesta en chat → confirm (approve/reject/edit) → audit
- API: `POST /agent/query` con `session_id`
- Docs: `docs/agent/agent-memory.md`, `CONTEXT-agent-memory.es.md`
- Evals: `tests/pipelines/test_agent_memory.py`

## MCP Server — company tools (OAuth)
- Paquete: `mcps/brasaland_tools/` (no bajo `services/`)
- Stack: FastMCP + **mcpauth** (resource server) + Streamable HTTP `:8100`
- Tools: `manage_incidents`, `query_inventory`, `mutate_inventory` (write reject)
- Scopes: `brasaland:tools`, `incidents:read|write`, `inventory:read`
- Agente cliente: `services/agent/tools/mcp_client.py` (`langchain-mcp-adapters`)
- Docs: `docs/mcp/mcp-oauth-tools.md`
- Evals: `tests/pipelines/test_mcp_server.py`

## LangGraph agent (Part 2/3 — external tools via MCP)
- Tools vía MCP (ya no IncidentRepository directo desde el agente)
- Routing: `classify_intent` → rag | ticket | inventory
- Fallback: `tool_fallback` (sin alucinar estado/stock)
- Docs: `docs/agent/langgraph-external-tools.md`
- Evals: `tests/pipelines/test_agent_tools.py`

## LangGraph agent (Part 1)
- Paquete: `services/agent/` (grafo compilado + checkpoint MemorySaver)
- Nodos separados: receive → retrieve → generate | refuse
- API: `POST /agent/query`, `GET /agent/traces/{run_id}`
- Traces: `data/eval/agent_traces/`
- Evals: `tests/pipelines/test_agent_graph.py`
- Docs: `docs/agent/langgraph-agent-base.md`

## RAG — Base de conocimiento Brasaland
- CONTEXT: `docs/rag/CONTEXT-brasaland.es.md`
- Corpus: `docs/company-knowledge-base/`
- Index: `data/process/rag.py` (`setup`, `embed`) → Qdrant `brasaland_knowledge`
- Pipeline: `data/pipelines/rag.py` (`retrieve`, `generate_answer`, `query`)
- API: `POST /knowledge/query` (`services/knowledge/`)
- UI: backoffice `/knowledge`
- Eval: `data/eval/test-queries.json` + `scripts/eval_rag_recall.py`
- Diseño: `docs/rag/rag-design.md`
- Infra: servicio `qdrant` en `docker-compose.yml` (`:6333`)

## Rama / PRs mergeados (ML & data)
- Pipeline resiliente: mergeado (#28)
- Subflows + dashboard: mergeado (#29)
- Script nocturno: mergeado (#30)
- Sentimiento WeLoveReviews: mergeado (#31)
- Eval regresión ventas: mergeado (#32)
- Forecast ventas (train): mergeado (#33)
- RAG knowledge base: mergeado (#35)
- Celery DEV-55: mergeado (#36)
- LangGraph agent base: #37 · external tools: #38
- MCP OAuth tools: #39
- Agent Memory: #40
- Agent Guardrails / Memory / RFP Parte 1: en **`main`** (#40–#42)
- Producto estable: **`main`**
- Idioma UI: español (`AGENTS.md` ley 9)
