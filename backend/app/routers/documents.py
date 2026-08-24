"""Router de documentos: upload, lista, descarga, expiración y eliminación."""
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document
from app.models.operation import Operation
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.pdf_inspector import inspect_pdf
from app.utils.event_log import append_event
from app.utils.file_safety import safe_filename, validate_mime_type, validate_extension
from app.utils.hashing import sha256_file

router = APIRouter()

MAX_BYTES = settings.max_file_size_mb * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Sube un documento al store local.
    - Valida MIME real (no solo extensión)
    - Genera nombre seguro
    - Calcula SHA-256
    - Inspecciona el PDF y genera advertencias
    - Registra en DB y audit log
    """
    # Leer primero para validar
    content = await file.read()

    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo: {settings.max_file_size_mb} MB",
        )
    if not content:
        raise HTTPException(status_code=422, detail="El archivo está vacío.")

    # Validar extensión y MIME
    try:
        validate_extension(file.filename or "")
        mime_type = validate_mime_type(content, Path(file.filename or "").suffix)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Nombre seguro + directorio único por documento
    doc_id = uuid.uuid4()
    safe_name = safe_filename(file.filename or "documento.pdf")
    doc_dir = settings.originals_dir / str(doc_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    dest_path = doc_dir / safe_name

    # Guardar archivo (inmutable — directorio con UUID)
    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(content)

    # Hash SHA-256
    file_hash = sha256_file(dest_path)

    # Inspección PDF
    inspection: dict = {}
    warnings_json = "[]"
    page_count = None
    is_encrypted = False
    has_forms = False
    has_signatures = False

    if mime_type == "application/pdf":
        try:
            inspection = inspect_pdf(dest_path)
            import json
            warnings_json = json.dumps(inspection.get("warnings", []))
            page_count = inspection.get("page_count")
            is_encrypted = inspection.get("is_encrypted", False)
            has_forms = inspection.get("has_forms", False)
            has_signatures = inspection.get("has_signatures", False)
        except Exception:
            pass  # Continuar aunque la inspección falle

    # Expiración por defecto
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.default_expiry_days)

    # Guardar en DB
    doc = Document(
        id=doc_id,
        filename_safe=safe_name,
        original_filename=file.filename or safe_name,
        original_path=str(dest_path),
        mime_type=mime_type,
        sha256=file_hash,
        size_bytes=len(content),
        page_count=page_count,
        is_encrypted=is_encrypted,
        has_forms=has_forms,
        has_signatures=has_signatures,
        warnings_json=warnings_json,
        expires_at=expires_at,
    )
    db.add(doc)
    await db.flush()

    # Audit log
    append_event(
        event_type="DOCUMENT_UPLOADED",
        doc_id=str(doc_id),
        details={
            "filename": file.filename,
            "safe_name": safe_name,
            "size_bytes": len(content),
            "mime_type": mime_type,
        },
        sha256_after=file_hash,
        ip_address=request.client.host if request.client else None,
    )

    return _doc_to_response(doc, inspection.get("warnings", []))


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Lista documentos activos (no eliminados ni expirados)."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Document)
        .where(Document.deleted_at.is_(None))
        .where(
            (Document.expires_at.is_(None)) | (Document.expires_at > now)
        )
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    docs = (await db.execute(stmt)).scalars().all()

    return DocumentListResponse(
        documents=[_doc_to_response(d) for d in docs],
        total=len(docs),
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await _get_doc_or_404(doc_id, db)
    return _doc_to_response(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Marca el documento como eliminado (soft delete). El original permanece."""
    doc = await _get_doc_or_404(doc_id, db)
    doc.deleted_at = datetime.now(timezone.utc)
    append_event(
        event_type="DOCUMENT_DELETED",
        doc_id=str(doc_id),
        details={"filename": doc.filename_safe},
        sha256_before=doc.sha256,
        ip_address=request.client.host if request.client else None,
    )


@router.get("/{doc_id}/download")
async def download_original(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Descarga el archivo original."""
    doc = await _get_doc_or_404(doc_id, db)
    path = Path(doc.original_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo original no encontrado en disco.")
    return FileResponse(
        path=str(path),
        filename=doc.filename_safe,
        media_type=doc.mime_type or "application/octet-stream",
    )


# ── Helpers ──────────────────────────────────────────────────────────

async def _get_doc_or_404(doc_id: uuid.UUID, db: AsyncSession) -> Document:
    doc = await db.get(Document, doc_id)
    if not doc or doc.deleted_at:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    return doc


def _doc_to_response(doc: Document, extra_warnings: list | None = None) -> DocumentResponse:
    import json
    from app.schemas.document import DocumentWarning
    try:
        stored = json.loads(doc.warnings_json or "[]")
    except Exception:
        stored = []
    all_warnings = (extra_warnings or []) + stored
    # Deduplicar por tipo
    seen = set()
    deduped = []
    for w in all_warnings:
        if w.get("type") not in seen:
            seen.add(w.get("type"))
            deduped.append(DocumentWarning(**w))
    return DocumentResponse(
        id=doc.id,
        filename_safe=doc.filename_safe,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        sha256=doc.sha256,
        size_bytes=doc.size_bytes,
        page_count=doc.page_count,
        is_encrypted=doc.is_encrypted,
        has_forms=doc.has_forms,
        has_signatures=doc.has_signatures,
        warnings=deduped,
        created_at=doc.created_at,
        expires_at=doc.expires_at,
        deleted_at=doc.deleted_at,
    )
