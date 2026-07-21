# Brasaland API

Backend FastAPI: autenticación JWT, usuarios/perfiles, proveedores e incidencias (TinyDB).

## Arranque rápido (para clase / demo)

Desde la **raíz del monorepo**, en orden:

```bash
# 1) Activar el entorno virtual de Python del monorepo
#    Aísla las dependencias del sistema; evita conflictos de versiones.
source .venv/bin/activate
# Si aún no existe el venv:
#   uv venv && source .venv/bin/activate

# 2) Instalar dependencias de la API (FastAPI, TinyDB, jose, passlib, etc.)
#    Usamos uv (no pip install suelto) según el estándar del proyecto.
uv pip install -r services/api/requirements.txt

# 3) Copiar plantilla de secretos a .env local
#    SECRET_KEY y caducidad del JWT viven aquí; .env NO se sube a GitHub.
cp services/api/.env.example services/api/.env

# 4) Entrar en el paquete de la API
cd services/api

# 5) Cargar usuario admin de prueba (email + password hasheada en TinyDB)
#    Necesario para poder hacer login y obtener un token JWT.
PYTHONPATH=. python seed_auth.py

# 6) Cargar los 15 proveedores del directorio (hito anterior)
#    Así /suppliers no arranca vacío en la demo.
PYTHONPATH=. python seed.py

# 7) Levantar la API en el puerto 8000 con recarga automática
#    Docs interactivos: http://localhost:8000/docs
#    Health público:     http://localhost:8000/health
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Qué demostrar después del arranque**

1. Abrir `/docs`
2. `POST /auth/login` con el admin del seeder (`username` = email)
3. Pulsar **Authorize** y pegar el `access_token`
4. Llamar `GET /suppliers` o `GET /auth/me` (con token → 200; sin token → 401)

---

## Requisitos

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv)

## Instalación completa de uv (solo la primera vez)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc   # o: source $HOME/.local/bin/env
uv venv
source .venv/bin/activate
uv pip install -r services/api/requirements.txt
cp services/api/.env.example services/api/.env
```

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

Requieren cabecera `Authorization: Bearer <token>` tras el login.
