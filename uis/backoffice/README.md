# Backoffice UI

Panel interno de operación Brasaland (`uis/backoffice`) con autenticación JWT.

## Auth (AUTH-02 + AUTH-03)

Rutas públicas:
- `/login` — incluye enlace «¿Olvidaste tu contraseña?»
- `/register`
- `/forgot-password` — mensaje genérico tras el envío (anti-enumeración)
- `/reset-password?token=...` — nueva contraseña; éxito → `/login?reset=ok`

Rutas protegidas (exigen token en `localStorage`):
- `/` (dashboard)
- `/proveedores`
- `/account/profile`
- `/account/change-password`

El token se guarda tras login/registro y se envía como `Authorization: Bearer <token>`.
Un **401** limpia la sesión y redirige a `/login`. **Cerrar sesión** hace lo mismo.

La web pública `uis/website` **no** tiene auth (permanece abierta).

## Arranque

1. API + seeders:

```bash
cd services/api
source ../../.venv/bin/activate
# Asegura RESEND_API_KEY / FRONTEND_URL en .env (ver services/api/.env.example)
PYTHONPATH=. python seed_auth.py
PYTHONPATH=. python seed.py
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Backoffice:

```bash
cd uis/backoffice
npm install
npm run dev
```

3. Abre `http://localhost:3000/login`  
   Admin seeder: `alfredobormujo@gmail.com` / (password del seeder)

4. Probar recuperación: `/forgot-password` → email o consola API → `/reset-password?token=...`

## Comandos

- `npm run dev`
- `npm run lint`
- `npm run build`
