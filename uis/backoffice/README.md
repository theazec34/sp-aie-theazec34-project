# Backoffice UI

Panel interno de operación Brasaland (`uis/backoffice`).

## Directorio de proveedores

Página: `/proveedores`

1. API + seeder:

```bash
cd services/api
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Backoffice:

```bash
cd uis/backoffice
cp .env.example .env.local
npm install
npm run dev
```

3. Abre `http://localhost:3000/proveedores`.

En Codespaces marca el puerto **8000** como Public y usa esa URL en el campo **URL API** si hace falta.

## Comandos

- `npm run dev`
- `npm run lint`
- `npm run build`

La web pública principal vive en `../website`. La UI de incidencias CSV vive en `../web` (también servida por la API en `/`).
