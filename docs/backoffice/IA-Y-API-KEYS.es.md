# IA Brasaland y API keys (para la sesión de mañana)

Documento de continuidad: cómo encaja la IA que ya programamos y qué variables hacen falta.

## Piezas ya en el monorepo

| Pieza | Dónde | Qué hace |
|-------|--------|----------|
| Agente LangGraph | `services/agent` + backoffice `/agent` | Chat con tools (MCP), RAG, memoria, guardrails |
| Base de conocimiento (RAG) | `services/knowledge` + `/knowledge` | Embeddings + Qdrant (`brasaland_knowledge`) |
| RFP intake / generación | `services/rfp` + `/rfp` | PDF → clasificar → secciones por depto → HITL |
| Memoria de agente | namespace `brasaland_agent_memory` | Episodios con confirmación explícita (nunca en `*_knowledge`) |
| MCP tools | `mcps/brasaland_tools` | Incidents + inventory vía OAuth; el agente no llama ORM directo |

## Variables de generación (chat / LLM)

En `.env` (raíz). Preferido: `GENERATION_*`. También se aceptan alias `LLM_*`
(`LLM_BASE_URL` → `GENERATION_BASE_URL`, `LLM_MODEL` → `GENERATION_MODEL_ID`, etc.).

```bash
# Sin clave: modo grounded (solo texto recuperado del RAG, sin LLM externo)
GENERATION_PROVIDER=grounded

# Con portal OpenAI-compatible (4Geeks):
GENERATION_PROVIDER=openai
GENERATION_BASE_URL=https://llm.4geeks.ai/v1
GENERATION_API_KEY=   # pégala solo en .env, nunca en el chat
GENERATION_MODEL_ID=madrid-spain/opnerouter/openai/gpt-6-luna

# Equivalente con alias:
# LLM_BASE_URL=https://llm.4geeks.ai/v1
# LLM_API_KEY=...
# LLM_MODEL=madrid-spain/opnerouter/openai/gpt-6-luna
```

Tras editar `.env`: `docker compose up -d --force-recreate backend`

### Codespaces: DNS del contenedor vs host

Si la key da **200 en el host** pero el backend falla:

| Síntoma en el contenedor | Causa | Remedio |
|--------------------------|--------|---------|
| `Could not resolve host` | DNS bridge | `bash scripts/codespace-fix-llm-dns.sh` |
| DNS OK + `curl …:443` timeout | Sin egress TCP | `bash scripts/codespace-enable-llm-proxy.sh` |

El proxy (`llm-proxy`, `network_mode: host`) escucha en `:18080` y el backend usa
`http://host.docker.internal:18080/v1` como `GENERATION_BASE_URL` / `EMBEDDING_BASE_URL`.

## Variables de embedding (RAG)

```bash
EMBEDDING_PROVIDER=fastembed   # local, sin API key
# o:
# EMBEDDING_PROVIDER=openai
# EMBEDDING_BASE_URL=https://<tu-gateway>
# EMBEDDING_API_KEY=...
# EMBEDDING_MODEL_ID=...
```

## Auth del panel vs keys de IA

- **Login backoffice** (`SECRET_KEY`, JWT, `SEED_ADMIN_*`) ≠ keys del LLM.
- Las API keys de generación/embedding solo las usa el **backend** (nunca el navegador).
- Sin `GENERATION_API_KEY`, agente/knowledge/RFP siguen vivos en modo **grounded** o con degradación documentada; no deben tumbar el login.

## Cómo probar mañana (orden)

1. `cp .env.example .env` y rellenar `SECRET_KEY` + opcionalmente `GENERATION_*`
2. `docker compose up --build`
3. Codespaces: puerto **8000 Public**; en login «Usar auto-detectada» (URL `…-8000…`)
4. Panel → Base de conocimiento / Agente / RFP con un PDF de `rfp-requests/brasaland/`

## Lecturas cortas

- `docs/agent/langgraph-agent-base.md`
- `docs/agent/langgraph-external-tools.md`
- `docs/rag/` (si existe CONTEXT)
- `docs/rfp/brasaland-BRIEFING.es.md`
