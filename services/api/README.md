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

Documentación interactiva: `http://localhost:8000/docs`

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servicio |
| `POST` | `/api/v1/incidents/analyze` | Sube un CSV y devuelve el resumen JSON |
| `POST` | `/api/v1/incidents/export` | Sube un CSV y descarga el resumen en CSV |

## Ejemplo

```bash
curl -X POST "http://localhost:8000/api/v1/incidents/analyze" \
  -F "file=@../../scripts/incidents-brasaland.csv"
```
