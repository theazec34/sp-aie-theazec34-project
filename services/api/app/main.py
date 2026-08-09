from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.analyzer import analyze_text, build_report, export_to_csv_text
from app.auth.deps import get_current_user
from app.auth.router import router as auth_router
from app.database import init_db
from app.errors import register_exception_handlers
from app.incidents.router import router as incidents_router
from app.inventory import models as _inventory_models  # noqa: F401 — register metadata
from app.inventory.router import router as inventory_router
from app.profiles.router import router as profiles_router
from app.schemas import AnalysisReport
from app.suppliers.router import router as suppliers_router
from app.users.models import UserInDB
from app.users.router import router as users_router

# services/api/app/main.py → monorepo root → uis/web
WEB_DIR = Path(__file__).resolve().parents[3] / "uis" / "web"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_db()
    except Exception as exc:  # noqa: BLE001 — boot must not hang if DB is unreachable
        # Auth/suppliers (TinyDB) still work; inventory routes will fail until DB is up.
        print(f"[startup] WARN — init_db skipped: {exc}", flush=True)
    yield


app = FastAPI(
    title="Brasaland API",
    version="1.3.0",
    description=(
        "API Brasaland Digital: auth JWT (TinyDB), inventario SQLModel "
        "(Postgres/Supabase o SQLite), proveedores e incidencias."
    ),
    lifespan=lifespan,
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
app.include_router(inventory_router)


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
        "inventory": {
            "products": "/inventory/products",
            "product_detail": "/inventory/products/{id}",
            "orders_inbound": "/inventory/orders/inbound",
            "orders_outbound": "/inventory/orders/outbound",
            "orders": "/inventory/orders",
            "auth_required": True,
            "user_uuid_note": "TinyDB numeric user id as string (e.g. '1')",
        },
    }


@app.post("/api/v1/incidents/analyze", response_model=AnalysisReport)
async def analyze_incidents(
    file: UploadFile = File(...),
    _current: UserInDB = Depends(get_current_user),
) -> AnalysisReport:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Se requiere un fichero CSV.")

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="El fichero CSV debe estar codificado en UTF-8.",
        ) from exc
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

    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="El fichero CSV debe estar codificado en UTF-8.",
        ) from exc
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
        raise HTTPException(
            status_code=500,
            detail="Interfaz de incidencias no disponible. Contacta con soporte.",
        )
    return FileResponse(index)


# CSS/JS y demás estáticos de uis/web (después de las rutas API)
if WEB_DIR.is_dir():
    app.mount("/static-ui", StaticFiles(directory=str(WEB_DIR)), name="web-static")


@app.get("/styles.css", include_in_schema=False)
def styles() -> FileResponse:
    path = WEB_DIR / "styles.css"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    return FileResponse(path)


@app.get("/app.js", include_in_schema=False)
def app_js() -> FileResponse:
    path = WEB_DIR / "app.js"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    return FileResponse(path)
