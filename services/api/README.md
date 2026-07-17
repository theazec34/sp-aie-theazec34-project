# Brasaland Incidents API

Backend FastAPI para analizar y exportar reportes de incidencias operativas.

## Requisitos

- Python 3.12+
- Dependencias en `requirements.txt`

## Instalación

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- UI (mismo puerto): `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- Docs: `http://localhost:8000/docs`

### Codespaces

1. Arranca solo el puerto **8000**.
2. En panel **Ports**, marca **8000** como **Public**.
3. Abre la URL pública del 8000 (no uses el 8080).
4. Pulsa **Probar API**; debe salir "API conectada".

Documentación interactiva: `http://localhost:8000/docs`

## Directorio de proveedores (TinyDB)

```bash
cd services/api
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/suppliers` | Alta de proveedor |
| `GET` | `/suppliers` | Listado (`?country=` / `?category=`) |
| `GET` | `/suppliers/{id}` | Detalle |
| `PATCH` | `/suppliers/{id}/rate` | Actualiza tarifa (+ `updated_at`) |
| `PATCH` | `/suppliers/{id}/status` | `active` / `suspended` |
| `DELETE` | `/suppliers/{id}` | Borrado (correcciones) |

## Endpoints de incidencias

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servicio |
| `POST` | `/api/v1/incidents/analyze` | Sube un CSV y devuelve el resumen JSON |
| `POST` | `/api/v1/incidents/export` | Sube un CSV y descarga el resumen en CSV |

## Ejemplo incidencias

```bash
curl -X POST "http://localhost:8000/api/v1/incidents/analyze" \
  -F "file=@../../scripts/incidents-brasaland.csv"
```
