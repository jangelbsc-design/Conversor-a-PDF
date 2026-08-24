"""Router de conversión Office → PDF."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.operation import Operation, OperationStatus, OperationType
from app.schemas.operation import OperationResponse
from app.services.pdf_convert import convert_to_pdf
from app.utils.event_log import append_event
from app.utils.file_safety import safe_filename, validate_mime_type, validate_extension, ALLOWED_OFFICE_MIME
from app.utils.hashing import sha256_file

router = APIRouter()

MAX_BYTES = settings.max_file_size_mb * 1024 * 1024


@router.post("/", response_model=OperationResponse, status_code=status.HTTP_201_CREATED)
async def convert_office_to_pdf(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Convierte un documento Office (.docx, .xlsx, .pptx, .odt, etc.) a PDF
    usando LibreOffice headless.
    """
    content = await file.read()

    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"Máximo {settings.max_file_size_mb} MB.")
    if not content:
        raise HTTPException(status_code=422, detail="Archivo vacío.")

    try:
        validate_extension(file.filename or "")
        mime_type = validate_mime_type(content, Path(file.filename or "").suffix)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if mime_type == "application/pdf":
        raise HTTPException(status_code=422, detail="El archivo ya es PDF. Usa otras herramientas.")

    if mime_type not in ALLOWED_OFFICE_MIME:
        raise HTTPException(status_code=422, detail=f"Tipo no soportado para conversión: {mime_type}")

    # Guardar temporalmente en outputs (no es un original inmutable)
    op = Operation(
        operation_type=OperationType.convert,
        input_paths=[file.filename or "input"],
        params_json={"original_mime": mime_type, "original_filename": file.filename},
        status=OperationStatus.running,
    )
    db.add(op)
    await db.flush()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    op_dir = settings.outputs_dir / str(op.id)
    op_dir.mkdir(parents=True, exist_ok=True)

    safe_name = safe_filename(file.filename or "documento")
    input_path = op_dir / f"input_{safe_name}"

    async with aiofiles.open(input_path, "wb") as f:
        await f.write(content)

    try:
        pdf_path = convert_to_pdf(input_path, op_dir)
        out_hash = sha256_file(pdf_path)

        op.status = OperationStatus.success
        op.output_path = str(pdf_path)
        op.output_sha256 = out_hash
        op.completed_at = datetime.now(timezone.utc)

        append_event(
            event_type="CONVERT_COMPLETED",
            operation_id=str(op.id),
            details={"original_filename": file.filename, "mime_type": mime_type},
            sha256_after=out_hash,
            ip_address=request.client.host if request.client else None,
        )

    except Exception as e:
        op.status = OperationStatus.failed
        op.error_message = str(e)
        op.completed_at = datetime.now(timezone.utc)
        raise HTTPException(status_code=500, detail=f"Error de conversión: {e}")

    return op


@router.get("/{operation_id}/download")
async def download_converted(operation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    op = await db.get(Operation, operation_id)
    if not op or op.operation_type != OperationType.convert:
        raise HTTPException(status_code=404, detail="Operación no encontrada.")
    if op.status != OperationStatus.success:
        raise HTTPException(status_code=400, detail=f"Estado: {op.status}")
    path = Path(op.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(path=str(path), filename=path.name, media_type="application/pdf")
