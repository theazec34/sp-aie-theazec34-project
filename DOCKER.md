# Docker — Brasaland Digital

Arranque reproducible de website, backoffice y API con un comando.

## Requisitos

- Docker Desktop o Docker Engine + Compose v2
- Archivo `.env` en la **raíz** del monorepo (copia desde `.env.example`)

```bash
cp .env.example .env
# Edita SECRET_KEY y, si usas inventario en Supabase, DATABASE_URL
```

## Arranque

```bash
docker compose up --build
```

| Servicio | Contenedor | URL en el host |
|----------|------------|----------------|
| Website (Next.js) | `brasaland-interfaces` | http://localhost:3000 |
| Backoffice (Next.js) | mismo contenedor | http://localhost:3001 |
| API FastAPI | `brasaland-backend` | http://localhost:8000 |
| Docs API | | http://localhost:8000/docs |

## Red Docker

- Red explícita: `brasaland-net`
- Nombre del servicio API: **`backend`** → URL interna `http://backend:8000` (`INTERNAL_API_URL`)
- El **navegador** del host no resuelve nombres Docker: usa `NEXT_PUBLIC_API_URL=http://localhost:8000`

## Hot reload

- `interfaces`: bind mount de `uis/website` y `uis/backoffice` + `next dev`
- `backend`: bind mount de `services/api` + `uvicorn --reload`

## Seeds

El entrypoint del backend ejecuta (idempotente) antes de uvicorn:

1. `seed_auth.py`
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

## Parar

```bash
docker compose down
# + volúmenes de datos TinyDB/node_modules:
# docker compose down -v
```
