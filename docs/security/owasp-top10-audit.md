# Auditoría OWASP Top 10 — Brasaland Digital

**Alcance:** backend FastAPI, frontends Next (website/backoffice), sistema agéntico (LangGraph + RAG + MCP + SSE/WS).  
**Fecha:** 2026-10-20 · **BRIEFING:** `docs/security/brasaland-BRIEFING-ai-secure.es.md`  
**Severidad crítica:** corregida en este PR con evidencia reproducible.

---

## 0. Baseline servidor / red

Captura previa a correcciones: `docs/security/evidence/baseline-cloud.txt`  
Scripts: `scripts/hardening/00-baseline.sh`, `10-apply-host.sh`, `20-verify.sh`.

| Control | Antes | Después |
| ------- | ----- | ------- |
| Redis `:6379` publicado al host | Sí (`docker-compose.yml`) | **No** — solo red `brasaland-net` |
| Qdrant `:6333/:6334` al host | Sí | **No** — solo red interna |
| Flower `:5555` | Público sin auth | **Loopback** `127.0.0.1:5555` + basic auth |
| Usuario no-root ops | No definido | Script crea `brasaland`; Compose documentado |
| SSH root | Depende del host | `PermitRootLogin no` vía `10-apply-host.sh` |
| Firewall | Ausente en cloud agent | UFW allow 22/80/443; deny Redis/Qdrant/MCP/DB |

Puertos expuestos a clientes: **3000/3001** (UI), **8000** (API; delante de TLS en prod). SSE/WS via API autenticada. **Bloqueados desde internet:** Redis, Qdrant, Flower (salvo loopback), MCP `:8100`, Postgres.

---

## Matriz OWASP Top 10 × capa

Leyenda: **Aplica / No aplica** · Criticidad · Evidencia · Fix

### A01 — Broken Access Control

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Backend | Sí | `/api/incidents` **sin JWT** (cualquiera en la red CRUD) | **CRITICAL FIXED** — `dependencies=[Depends(get_current_user)]` en `incidents/router.py` |
| Backend | Sí | Suspender/borrar proveedor sin confirm ni rol | **CRITICAL FIXED** — `require_admin` + `confirm=true` |
| Frontend | Sí | `skipAuth: true` en listado/resumen incidencias | **FIXED** — usa JWT vía `apiFetch` |
| Agente | Sí | ¿Tools MCP escritura inventario / Points? | **OK** — `mutate_inventory` → 403; sin scope `inventory:write`; sin API Points |
| Evidencia | | `test_incidents_require_jwt`, `test_supplier_irreversible.py`, `test_mcp_server.py` |

### A02 — Cryptographic Failures

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Backend | Sí | Password admin hardcodeado en `seed_auth.py` | **CRITICAL FIXED** — solo `SEED_ADMIN_*` env |
| Backend | Sí | `SECRET_KEY` obligatorio (falla si falta) | **OK** — `auth/config.py` |
| Agente | Sí | API keys LLM / MCP | Solo `.env`; MCP dev secret documentado → prod `MCP_AUTH_MODE=oidc` |
| Frontend | Parcial | JWT en `localStorage` / WS `?token=` | Aceptable backoffice; riesgo log Referer documentado |
| Evidencia | | `scripts/hardening/20-verify.sh` (seed_auth), `.env.example` |

### A03 — Injection

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Backend | Sí | TinyDB/SQLModel parametrizados | **OK** |
| Agente | Sí | Prompt injection directa / RAG | Guardrails input + aislamiento RAG; test Brasa Points + RAG poison |
| Frontend | Bajo | React escapa XSS por defecto | **OK** |
| Evidencia | | `test_brasa_points_cross_customer_exfil_blocked`, `test_rag_injection_isolated_never_as_system` |

### A04 — Insecure Design

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Agente | Sí | Acciones irreversibles sin humano | Confirm admin proveedores; MCP read-only inventario; sin campañas masivas |
| Backend | Sí | Excessive agency API | Documentado; inventory JWT; agent no escribe |
| Evidencia | | `nist-ai-secure-practices.md` §3 |

### A05 — Security Misconfiguration

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Infra | Sí | Redis/Qdrant/Flower abiertos | **CRITICAL FIXED** — compose endurecido |
| Agente | Sí | MCP `0.0.0.0:8100` + mode=dev | No en Compose; docs exige oidc en prod |
| Backend | Sí | `/docs` OpenAPI en dev | Aceptable local; desactivar detrás de gateway en prod |
| Evidencia | | `docker-compose.yml`, `20-verify.sh` |

### A06 — Vulnerable and Outdated Components

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Backend/UI | Sí | Deps vía `uv` / npm lockfiles | Proceso: `uv lock` / `npm audit` en CI (recomendado) |
| Agente | Sí | LangGraph / MCP libs | Mismas pipelines de deps |
| Evidencia | | `pyproject.toml`, `uv.lock` |

### A07 — Identification and Authentication Failures

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Backend | Sí | JWT OAuth2 password flow | **OK** — bcrypt, expiry |
| SSE/WS | Sí | Auth requerida | **OK** — Bearer / `?token=` |
| Agente | Sí | `/agent/query` JWT | **OK** |
| Evidencia | | `test_rfp_sse.py`, `test_agent_chat_ws.py` |

### A08 — Software and Data Integrity Failures

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Backend | Parcial | Seeds / CI | Imágenes Compose versionadas; sin unsigned hooks |
| Agente | Sí | Memoria episódica | Confirmación explícita approve/reject |
| Evidencia | | `docs/agent/agent-memory.md` |

### A09 — Security Logging and Monitoring Failures

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Agente | Sí | Guardrail activations | `guardrail_summary` + logs harness |
| Backend | Parcial | Timing middleware | Telemetry events; ampliar alertas SIC/FIPA en ops |
| Evidencia | | `GET /agent/guardrails/summary` |

### A10 — Server-Side Request Forgery

| Capa | Aplica | Hallazgo | Fix / estado |
| ---- | ------ | -------- | ------------ |
| Backend | Bajo | Pocas URLs user-controlled | Resend/Qdrant por env fijo |
| Agente | Bajo | MCP client a URL configurada | **OK** — no URL libre del usuario |
| Evidencia | | `MCP_URL` / env |

---

## Sistema agéntico — foco BRIEFING

| Chequeo | Resultado |
| ------- | --------- |
| A01 tools escritura vs inventario lectura | MCP `mutate_inventory` siempre 403; sin `inventory:write` |
| A01 chat → pedidos / Brasa Points | No hay tools de Points ni de PO masivo |
| A02 API keys | Fuera de repo; seed admin vía env |
| A05 permisos agente | Corre como servicio API JWT; MCP scopes mínimos |

---

## Correcciones críticas — evidencia

### C1 — Incidents sin auth

```bash
# Antes: 200/201 sin token. Después:
cd services/api && PYTHONPATH=. uv run pytest tests/test_incidents.py::test_incidents_require_jwt -q
# → 401/403 sin Authorization
```

### C2 — Password en seed_auth

```bash
grep -E 'ADMIN_PASSWORD\s*=' services/api/seed_auth.py   # vacío / solo getenv
bash scripts/hardening/20-verify.sh   # PASS seed_auth
```

### C3 — Puertos internos

```bash
bash scripts/hardening/20-verify.sh
# PASS Redis/Qdrant sin ports; Flower 127.0.0.1
```

### C4 — Proveedor irreversible

```bash
cd services/api && PYTHONPATH=. uv run pytest tests/test_supplier_irreversible.py -q
```

### C5 — Prompt injection Brasa Points

```bash
uv run pytest tests/pipelines/test_agent_guardrails.py::test_brasa_points_cross_customer_exfil_blocked -q
```

---

## Respuesta a incidentes (Ley 1581 + FIPA)

1. Contener (revocar JWT/`SECRET_KEY`, cerrar puertos, rotar API keys).  
2. Evaluar si hay datos personales de clientes/empleados.  
3. **Colombia:** notificar SIC a la mayor brevedad.  
4. **Florida:** notificar afectados (+ AG si aplica) ≤ **30 días**.  
5. Post-mortem en `docs/security/`.

---

## Cómo reproducir la verificación completa

```bash
bash scripts/hardening/20-verify.sh
cd services/api && PYTHONPATH=. uv run pytest tests/test_incidents.py tests/test_supplier_irreversible.py tests/test_cache.py -q
uv run pytest tests/pipelines/test_agent_guardrails.py tests/pipelines/test_mcp_server.py -q
```
