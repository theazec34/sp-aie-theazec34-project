# Docker — Brasaland Digital

Arranque reproducible de website, backoffice y API con un comando.

## Requisitos

- Docker Desktop o Docker Engine + Compose v2
- Archivo `.env` en la **raíz** del monorepo (copia desde `.env.example`)

```bash
cp .env.example .env
# Edita SECRET_KEY y, si usas inventario en Supabase, DATABASE_URL
```

> **Codespaces / Linux:** si `cp -n` avisa de portabilidad, usa `cp .env.example .env` (sin `-n`) o `cp --update=none .env.example .env`.

## Arranque

Desde la **raíz** del monorepo (donde está `docker-compose.yml`):

```bash
docker compose up --build
```

### Error BuildKit: `parent snapshot … does not exist: not found`

Caché corrupta del builder (frecuente en Codespaces). **No es un fallo del Dockerfile.** Limpia y reconstruye:

```bash
docker compose down
docker builder prune -af
docker compose build --no-cache
docker compose up
```

Atajo: `bash scripts/docker-rebuild-clean.sh`

Si sigue fallando: `DOCKER_BUILDKIT=0 docker compose build --no-cache && docker compose up`.

### BrasAI: `Storage folder … qdrant_local is already accessed`

Qdrant **local** (fichero) no admite dos clientes a la vez. Con
`QDRANT_FORCE_LOCAL=1` + `uvicorn --reload`, Reindexar/preguntar falla.

```bash
# En .env:
QDRANT_FORCE_LOCAL=0
# Compose ya pone QDRANT_URL=http://qdrant:6333
docker compose up -d --force-recreate backend qdrant
```

### Codespaces: LLM / `llm.4geeks.ai`

Dos fallos distintos en el contenedor `backend`:

1. **DNS** — `getent hosts llm.4geeks.ai` vacío → `extra_hosts` / `scripts/codespace-fix-llm-dns.sh`
2. **Egress TCP** — DNS OK pero `curl …:443` hace **timeout** (el host sí da 200) → el bridge no sale a internet.

Para (2) usa el proxy en red del host (`llm-proxy` → `:18080`):

```bash
bash scripts/codespace-enable-llm-proxy.sh
# deja GENERATION_BASE_URL / EMBEDDING_BASE_URL = http://host.docker.internal:18080/v1
docker compose exec -T backend python -c "from data.process.rag import setup; print(setup(recreate=True))"
```

El `.dockerignore` de raíz **debe** dejar pasar `data/`, `docs/company-knowledge-base/` y `docs/rfp/` (el `Dockerfile` hace `COPY` de esas rutas). Si el build falla con `"/docs/rfp": not found`, actualiza `main` o revisa que no hayas excluido `docs` enteros en `.dockerignore`.

| Servicio | Contenedor | URL en el host |
|----------|------------|----------------|
| Website (Next.js) | `brasaland-interfaces` | http://localhost:3000 |
| Backoffice (Next.js) | mismo contenedor | http://localhost:3001 |
| API FastAPI | `brasaland-backend` | http://localhost:8000 |
| Docs API | | http://localhost:8000/docs |
| Redis (broker Celery) | `brasaland-redis` | **solo red Docker** (no publicado al host) |
| Celery worker | `brasaland-worker` | (sin puerto HTTP) |
| Flower | `brasaland-flower` | http://127.0.0.1:5555 (loopback + basic auth) |
| Qdrant | `brasaland-qdrant` | **solo red Docker** (`http://qdrant:6333` desde backend) |

## Red Docker

- Red explícita: `brasaland-net`
- Nombre del servicio API: **`backend`** → URL interna `http://backend:8000` (`INTERNAL_API_URL`)
- Website y backoffice: el **navegador** llama a `/api-backend/*` (rewrite Next → `INTERNAL_API_URL`). No hace falta exponer `localhost:8000` al browser salvo WebSocket del agente o `NEXT_PUBLIC_API_DIRECT=1`.

## Hot reload

- `interfaces`: bind mount de `uis/website` y `uis/backoffice` + `next dev`
- `backend`: bind mount de `services/api` + `uvicorn --reload`

## Seeds

El entrypoint del backend ejecuta (idempotente) antes de uvicorn:

1. `seed_auth.py` (requiere `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` en el entorno)
2. `seed.py` (proveedores)
3. `seed_inventory.py` (con timeout; no bloquea el arranque)

## Supabase / SQLite

- Si `DATABASE_URL` es alcanzable → inventario en Postgres/Supabase.
- Si no (firewall, proyecto pausado, etc.) → **fallback automático a SQLite** en el volumen `backend_data`.
- Queda un marcador `services/api/data/.sqlite_fallback` (dentro del volumen). Bórralo para reintentar Supabase:

```bash
docker compose exec backend rm -f /app/api/data/.sqlite_fallback
docker compose restart backend
```

## Secretos

- `.env` está en `.gitignore` — no lo subas a GitHub
- No hay claves en `Dockerfile` ni en `docker-compose.yml`
- Si un secreto se filtra, rótalo (Supabase / Resend / `SECRET_KEY`)

## Celery worker (DEV-55)

El worker es un proceso **independiente** de FastAPI. Con Compose ya arranca
`worker` + `redis` + `flower`. En local:

```bash
# Terminal A — broker
redis-server --maxmemory-policy noeviction

# Terminal B — API
cd services/api && uv run uvicorn app.main:app --reload --port 8000

# Terminal C — worker (desde la carpeta services/)
cd services
PYTHONPATH=. uv run celery -A celery_app.celery worker --loglevel=INFO

# Terminal D — Flower (opcional)
cd services
PYTHONPATH=. uv run celery -A celery_app.celery flower --port=5555
```

Parar worker: `Ctrl+C` en su terminal (o `docker compose stop worker`).

`POST /api/v1/incidents/analyze` responde **202** + `task_id`; el resultado se
consulta en `GET /tasks/{task_id}`. Flower: http://localhost:5555

## Parar

```bash
docker compose down
# + volúmenes de datos TinyDB/node_modules:
# docker compose down -v
```
