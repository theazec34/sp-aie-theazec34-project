from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.analyzer import analyze_text, build_report, export_to_csv_text
from app.schemas import AnalysisReport

app = FastAPI(
    title="Brasaland Incidents API",
    version="1.0.0",
    description="Análisis y exportación de reportes de incidencias operativas.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "brasaland-incidents-api"}


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
