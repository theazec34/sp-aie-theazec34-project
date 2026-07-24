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
- `/incidents/nueva` — registrar incidencia (API pública, UI con sesión)
- `/incidents` — panel con filtros y cambio de estado
- `/incidents/resumen` — métricas agregadas
- `/account/profile`
- `/account/change-password`

El token se guarda tras login/registro y se envía como `Authorization: Bearer <token>`.
Un **401** limpia la sesión y redirige a `/login`. **Cerrar sesión** hace lo mismo.
Las llamadas a `/api/incidents*` usan `skipAuth` (endpoints públicos).

La web pública `uis/website` **no** tiene auth (permanece abierta).

## Arranque

1. API + seeders:

```bash
cd /workspaces/sp-aie-theazec34-project   # o raíz del monorepo
source .venv/bin/activate
# Asegura RESEND_API_KEY / FRONTEND_URL en .env (ver services/api/.env.example)
cd services/api
PYTHONPATH=. python seed_auth.py
PYTHONPATH=. python seed.py
cd ../..
python scripts/seed_incidents.py
cd services/api
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

4. Incidencias: `/incidents/nueva`, `/incidents`, `/incidents/resumen`

## Comandos

- `npm run dev`
- `npm run lint`
- `npm run build`
