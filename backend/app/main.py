"""
PDF Suite Local — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
from app.routers import (
    documents,
    merge,
    split,
    compress,
    convert,
    watermark,
    redact,
    ocr,
    rotate,
    reorder,
    preview,
    signatures,
    audit,
    backup,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea tablas si no existen (en Docker, Alembic ya las crea antes)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="PDF Suite Local",
    description=(
        "⚠️ Reemplazo personal de ILovePDF — completamente local. "
        "Sin telemetría, sin cuentas cloud, sin subida de archivos a terceros. "
        "USO DE BAJO RIESGO: no produce firmas electrónicas cualificadas."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ────────────────────────────────────────────────────────────
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────
app.include_router(documents.router, prefix="/api/documents", tags=["Documentos"])
app.include_router(merge.router,     prefix="/api/merge",     tags=["Merge"])
app.include_router(split.router,     prefix="/api/split",     tags=["Split"])
app.include_router(compress.router,  prefix="/api/compress",  tags=["Compress"])
app.include_router(convert.router,   prefix="/api/convert",   tags=["Convert"])
app.include_router(watermark.router, prefix="/api/watermark", tags=["Watermark"])
app.include_router(redact.router,    prefix="/api/redact",    tags=["Redact"])
app.include_router(ocr.router,       prefix="/api/ocr",       tags=["OCR"])
app.include_router(rotate.router,    prefix="/api/rotate",    tags=["Rotate"])
app.include_router(reorder.router,   prefix="/api/reorder",   tags=["Reorder"])
app.include_router(preview.router,   prefix="/api/preview",   tags=["Preview"])
app.include_router(signatures.router,prefix="/api/signatures",tags=["Signatures"])
app.include_router(audit.router,     prefix="/api/audit",     tags=["Audit"])
app.include_router(backup.router,    prefix="/api/backup",    tags=["Backup"])


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})
