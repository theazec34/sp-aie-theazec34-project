from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.analyzer import analyze_text, build_report, export_to_csv_text
from app.schemas import AnalysisReport
from app.suppliers.router import router as suppliers_router

# services/api/app/main.py → monorepo root → uis/web
WEB_DIR = Path(__file__).resolve().parents[3] / "uis" / "web"

app = FastAPI(
    title="Brasaland API",
    version="1.1.0",
    description=(
        "API Brasaland Digital: análisis de incidencias y directorio de proveedores "
        "(TinyDB)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(suppliers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "brasaland-api"}


@app.get("/api")
def api_info() -> dict[str, object]:
    return {
        "service": "brasaland-api",
        "health": "/health",
        "docs": "/docs",
        "ui_incidents": "/",
        "incidents": {
            "analyze": "/api/v1/incidents/analyze",
            "export": "/api/v1/incidents/export",
        },
        "suppliers": {
            "list_create": "/suppliers",
            "detail": "/suppliers/{id}",
            "rate": "/suppliers/{id}/rate",
            "status": "/suppliers/{id}/status",
        },
    }


@app.post("/api/v1/incidents/analyze", response_model=AnalysisReport)
async def analyze_incidents(file: UploadFile = File(...)) -> AnalysisReport:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Se requiere un fichero CSV.")

    content = (await file.read()).decode("utf-8")
    if not content.strip():
        raise HTTPException(status_code=400, detail="El fichero CSV está vacío.")

    result = analyze_text(content, file.filename)
    report = build_report(result)
    return AnalysisReport(**report)


@app.post("/api/v1/incidents/export")
async def export_incidents(file: UploadFile = File(...)) -> PlainTextResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Se requiere un fichero CSV.")

    content = (await file.read()).decode("utf-8")
    if not content.strip():
        raise HTTPException(status_code=400, detail="El fichero CSV está vacío.")

    result = analyze_text(content, file.filename)
    csv_text = export_to_csv_text(result)
    stem = file.filename.rsplit(".", 1)[0]
    filename = f"{stem}-analysis.csv"

    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/", include_in_schema=False)
def serve_ui() -> FileResponse:
    index = WEB_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=500, detail=f"UI no encontrada en {WEB_DIR}")
    return FileResponse(index)


# CSS/JS y demás estáticos de uis/web (después de las rutas API)
if WEB_DIR.is_dir():
    app.mount("/static-ui", StaticFiles(directory=str(WEB_DIR)), name="web-static")


@app.get("/styles.css", include_in_schema=False)
def styles() -> FileResponse:
    return FileResponse(WEB_DIR / "styles.css")


@app.get("/app.js", include_in_schema=False)
def app_js() -> FileResponse:
    return FileResponse(WEB_DIR / "app.js")
