# Brasaland Incidents Web

Interfaz web para cargar un CSV de incidencias, consultar el resumen y exportar resultados.

## Requisitos

- API en ejecución (`services/api`)
- Servidor estático para esta carpeta

## Uso local

Terminal 1 — API:

```bash
cd services/api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 — interfaz web:

```bash
cd uis/web
python3 -m http.server 8080
```

Abre `http://localhost:8080` y confirma que la URL de la API apunta a `http://localhost:8000`.

## Flujo

1. Arrastra o selecciona `incidents-brasaland.csv`.
2. Pulsa **Analizar incidencias** para ver el resumen en pantalla.
3. Pulsa **Descargar resumen CSV** para exportar `metric`, `value`, `percentage`.

## Estructura

```text
uis/web/
├── index.html
├── styles.css
├── app.js
└── README.md
```
