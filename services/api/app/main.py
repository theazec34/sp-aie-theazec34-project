from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.analyzer import analyze_text, build_report, export_to_csv_text
from app.auth.deps import get_current_user
from app.auth.router import router as auth_router
from app.errors import register_exception_handlers
from app.incidents.router import router as incidents_router
from app.profiles.router import router as profiles_router
from app.schemas import AnalysisReport
from app.suppliers.router import router as suppliers_router
from app.users.models import UserInDB
from app.users.router import router as users_router

# services/api/app/main.py → monorepo root → uis/web
WEB_DIR = Path(__file__).resolve().parents[3] / "uis" / "web"

app = FastAPI(
    title="Brasaland API",
    version="1.2.0",
    description=(
        "API Brasaland Digital: auth JWT, usuarios/perfiles, proveedores e incidencias "
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

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(suppliers_router)
app.include_router(incidents_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "brasaland-api"}


@app.get("/api")
def api_info() -> dict[str, object]:
    return {
        "service": "brasaland-api",
        "health": "/health",
        "docs": "/docs",
        "auth": {"login": "/auth/login", "me": "/auth/me"},
        "users": "/users",
        "profiles": "/profiles/me",
        "ui_incidents": "/",
        "incidents": {
            "analyze": "/api/v1/incidents/analyze",
            "export": "/api/v1/incidents/export",
            "crud": "/api/incidents",
            "summary": "/api/incidents/summary",
            "auth_required": False,
        },
        "suppliers": {
            "list_create": "/suppliers",
            "detail": "/suppliers/{id}",
            "rate": "/suppliers/{id}/rate",
            "status": "/suppliers/{id}/status",
            "auth_required": True,
        },
    }


@app.post("/api/v1/incidents/analyze", response_model=AnalysisReport)
async def analyze_incidents(
    file: UploadFile = File(...),
    _current: UserInDB = Depends(get_current_user),
) -> AnalysisReport:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Se requiere un fichero CSV.")

    content = (await file.read()).decode("utf-8")
    if not content.strip():
        raise HTTPException(status_code=400, detail="El fichero CSV está vacío.")

    result = analyze_text(content, file.filename)
    report = build_report(result)
    return AnalysisReport(**report)


@app.post("/api/v1/incidents/export")
async def export_incidents(
    file: UploadFile = File(...),
    _current: UserInDB = Depends(get_current_user),
) -> PlainTextResponse:
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
