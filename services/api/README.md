# Brasaland API

Backend FastAPI: autenticación JWT (TinyDB), inventario SQLModel (Postgres/Supabase o SQLite), proveedores e incidencias.

## Arranque rápido (para clase / demo)

Desde la **raíz del monorepo**, en orden:

```bash
# 1) Activar el entorno virtual de Python del monorepo
#    Aísla las dependencias del sistema; evita conflictos de versiones.
source .venv/bin/activate
# Si aún no existe el venv:
#   uv venv && source .venv/bin/activate

# 2) Instalar dependencias de la API (FastAPI, TinyDB, SQLModel, jose, passlib, etc.)
#    Usamos uv (no pip install suelto) según el estándar del proyecto.
uv pip install -r services/api/requirements.txt

# 3) Copiar plantilla de secretos a .env local
#    SECRET_KEY, JWT y opcional DATABASE_URL (Supabase); .env NO se sube a GitHub.
cp services/api/.env.example services/api/.env
# Opcional: pega la URI Transaction pooler de Supabase en DATABASE_URL.
# Si DATABASE_URL queda vacío → SQLite local en services/api/data/inventory.db

# 4) Entrar en el paquete de la API
cd services/api

# 5) Cargar usuario admin de prueba (email + password hasheada en TinyDB)
#    Necesario para poder hacer login y obtener un token JWT.
PYTHONPATH=. python seed_auth.py

# 6) Cargar los 15 proveedores del directorio (hito anterior)
#    Así /suppliers no arranca vacío en la demo.
PYTHONPATH=. python seed.py

# 7) Sembrar inventario demo (CONTEXT: 6 ingredientes, entradas y salidas)
PYTHONPATH=. python seed_inventory.py

# 8) Levantar la API en el puerto 8000 con recarga automática
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
| `POST` | `/auth/forgot-password` | Público | Siempre 200; envía email con enlace si el usuario existe |
| `POST` | `/auth/reset-password` | Público | `{ token, new_password }` — valida JWT+jti, actualiza e invalida |
| `POST` | `/auth/change-password` | Token | `{ current_password, new_password }` — 400 si la actual falla |
| `POST` | `/users` | Público | Registro (role default `user` + Profile opcional) |
| `GET` | `/users` | Token | Listado |
| `GET` | `/users/{id}` | Token | Detalle |
| `PUT` | `/users/{id}` | Token | email/role (self o admin; role solo admin) |
| `DELETE` | `/users/{id}` | Token | Borra user + profile (self o admin) |
| `GET/PUT` | `/profiles/me` | Token | Perfil del usuario autenticado |

### Recuperación de contraseña (AUTH-03) — Resend

Servicio elegido: **Resend**. Variables en `services/api/.env` (ver `.env.example`):

| Variable | Uso |
|----------|-----|
| `RESEND_API_KEY` | API key de Resend (nunca en el código) |
| `RESEND_FROM_EMAIL` | Remitente (p. ej. `Brasaland OPS <onboarding@resend.dev>`) |
| `FRONTEND_URL` | Base del backoffice para el enlace `/reset-password?token=...` |
| `RESET_TOKEN_EXPIRE_MINUTES` | Caducidad del token (15–60; default 30) |

Sin `RESEND_API_KEY`, el enlace se imprime en la consola de uvicorn (útil en clase). Con clave, se envía un email HTML vía `https://api.resend.com/emails`.

Siguen públicas: `/health`, `/docs`, `/`, `POST /auth/login`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /users`.

### Rutas existentes ahora protegidas (≥5)

- `POST/GET /suppliers`
- `GET/PATCH/DELETE /suppliers/{id}` (+ rate/status)
- `POST /api/v1/incidents/analyze`
- `POST /api/v1/incidents/export`
- `POST /auth/change-password`

### Verificación rápida en `/docs`

1. `POST /users` o usar el admin del seeder  
2. `POST /auth/login` (Authorize con el token)  
3. Llamar `GET /suppliers` / `GET /auth/me`  
4. Sin token → **401**
5. `POST /auth/forgot-password` con un email registrado → revisar Resend o consola
6. `POST /auth/reset-password` con el token del enlace
7. `POST /auth/change-password` con Bearer + contraseñas

## Inventario (SQLModel / dual DB)

CONTEXT: `05-backend-inventory-orm/CONTEXT-brasaland.es.md`

| Método | Ruta | Acceso | Descripción |
|--------|------|--------|-------------|
| `GET` | `/inventory/products` | JWT | Lista ingredientes + `current_stock` calculado |
| `POST` | `/inventory/products` | JWT | Crea ingrediente |
| `GET` | `/inventory/products/{id}` | JWT | Detalle + stock |
| `POST` | `/inventory/orders/inbound` | JWT | Entrada de proveedor |
| `POST` | `/inventory/orders/outbound` | JWT | Consumo/merma (400 si stock insuficiente) |
| `GET` | `/inventory/orders` | JWT | Entradas + salidas con datos del ingrediente |

### Dual database
- **TinyDB** (`data/auth.json`, etc.): usuarios, perfiles, proveedores, incidencias.
- **SQL / Supabase** (`DATABASE_URL`): tablas `ingredient`, `ingredient_entry`, `ingredient_exit`.
- **Sin tabla User en SQL.** El campo `user_uuid` de las órdenes es el **id numérico TinyDB como string** (ej. `"1"`), no un UUID de Supabase Auth.
- `current_stock` **nunca se almacena**: `sum(entries) − sum(exits)`.

### Conectar Supabase
1. Dashboard del proyecto → **Connect** → **Transaction pooler** → URI `postgresql://...`
2. Pegarla en `services/api/.env` como `DATABASE_URL=...` (nunca committear `.env`)
3. Reiniciar uvicorn; `init_db()` crea las tablas al arrancar.
4. `PYTHONPATH=. python seed_inventory.py`

## Proveedores e incidencias

Requieren cabecera `Authorization: Bearer <token>` tras el login.
