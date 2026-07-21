# Brasaland API

Backend FastAPI: autenticación JWT, usuarios/perfiles, proveedores e incidencias (TinyDB).

## Requisitos

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv)

## Instalación (uv)

Desde la **raíz del monorepo**:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc   # o: source $HOME/.local/bin/env
uv venv
source .venv/bin/activate
uv pip install -r services/api/requirements.txt
```

Configura secretos (no se suben a git):

```bash
cp services/api/.env.example services/api/.env
# edita SECRET_KEY en production
```

Seeders:

```bash
cd services/api
PYTHONPATH=. python seed_auth.py   # admin alfredobormujo@gmail.com
PYTHONPATH=. python seed.py        # 15 proveedores
```

## Ejecución

```bash
cd services/api
source ../../.venv/bin/activate
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Docs: `http://localhost:8000/docs`
- Health (público): `http://localhost:8000/health`

## Auth JWT

| Método | Ruta | Acceso | Descripción |
|--------|------|--------|-------------|
| `POST` | `/auth/login` | Público | Form OAuth2: `username`=email, `password` → JWT |
| `GET` | `/auth/me` | Token | email, role + profile |
| `POST` | `/users` | Público | Registro (role default `user` + Profile opcional) |
| `GET` | `/users` | Token | Listado |
| `GET` | `/users/{id}` | Token | Detalle |
| `PUT` | `/users/{id}` | Token | email/role (self o admin; role solo admin) |
| `DELETE` | `/users/{id}` | Token | Borra user + profile (self o admin) |
| `GET/PUT` | `/profiles/me` | Token | Perfil del usuario autenticado |

### Rutas existentes ahora protegidas (≥5)

- `POST/GET /suppliers`
- `GET/PATCH/DELETE /suppliers/{id}` (+ rate/status)
- `POST /api/v1/incidents/analyze`
- `POST /api/v1/incidents/export`

Siguen públicas: `/health`, `/docs`, `/`, `POST /auth/login`, `POST /users`.

### Verificación rápida en `/docs`

1. `POST /users` o usar el admin del seeder  
2. `POST /auth/login` (Authorize con el token)  
3. Llamar `GET /suppliers` / `GET /auth/me`  
4. Sin token → **401**

## Proveedores e incidencias

Ver tablas anteriores; requieren `Authorization: Bearer <token>`.
