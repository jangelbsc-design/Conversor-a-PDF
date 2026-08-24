"""Router de OCR."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document
from app.models.operation import Operation, OperationStatus, OperationType
from app.schemas.operation import OperationResponse
from app.services.pdf_ocr import run_ocr
from app.utils.event_log import append_event
from app.utils.hashing import sha256_file

router = APIRouter()


@router.post("/", response_model=OperationResponse)
async def apply_ocr(
    request: Request,
    doc_id: Annotated[uuid.UUID, Body(embed=True)],
    language: Annotated[str, Body(embed=True)] = "spa",
    deskew: Annotated[bool, Body(embed=True)] = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Aplica OCR al PDF usando ocrmypdf + tesseract.
    Idiomas disponibles: 'spa', 'eng', 'spa+eng', etc.
    """
    doc = await db.get(Document, doc_id)
    if not doc or doc.deleted_at:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    if doc.is_encrypted:
        raise HTTPException(status_code=422, detail="El documento está cifrado.")

    in_path = Path(doc.original_path)
    if not in_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco.")

    # Validar idioma (prevenir inyección de comandos)
    import re
    if not re.match(r'^[a-z]{2,4}(\+[a-z]{2,4})*$', language):
        raise HTTPException(status_code=422, detail=f"Idioma inválido: {language}")

    op = Operation(
        doc_id=doc_id,
        operation_type=OperationType.ocr,
        input_paths=[str(in_path)],
        params_json={"language": language, "deskew": deskew},
        status=OperationStatus.running,
    )
    db.add(op)
    await db.flush()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = settings.outputs_dir / str(op.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ocr_{language}_{ts}.pdf"

    try:
        ocr_result = run_ocr(in_path, out_path, language=language, deskew=deskew)
        out_hash = sha256_file(out_path)

        op.status = OperationStatus.success
        op.output_path = str(out_path)
        op.output_sha256 = out_hash
        op.completed_at = datetime.now(timezone.utc)
        op.params_json = {**op.params_json, **ocr_result}

        append_event(
            event_type="OCR_COMPLETED",
            doc_id=str(doc_id), operation_id=str(op.id),
            details=ocr_result,
            sha256_before=doc.sha256, sha256_after=out_hash,
            ip_address=request.client.host if request.client else None,
        )
    except Exception as e:
        op.status = OperationStatus.failed
        op.error_message = str(e)
        op.completed_at = datetime.now(timezone.utc)
        raise HTTPException(status_code=500, detail=f"Error de OCR: {e}")

    return op


@router.get("/{operation_id}/download")
async def download_ocr(operation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    op = await db.get(Operation, operation_id)
    if not op or op.operation_type != OperationType.ocr:
        raise HTTPException(status_code=404, detail="Operación no encontrada.")
    if op.status != OperationStatus.success:
        raise HTTPException(status_code=400, detail=f"Estado: {op.status}")
    path = Path(op.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(path=str(path), filename=path.name, media_type="application/pdf")
