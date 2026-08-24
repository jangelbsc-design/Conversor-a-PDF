"""Router de watermark."""
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
from app.services.pdf_watermark import add_text_watermark
from app.utils.event_log import append_event
from app.utils.hashing import sha256_file

router = APIRouter()


@router.post("/", response_model=OperationResponse)
async def add_watermark(
    request: Request,
    doc_id: Annotated[uuid.UUID, Body(embed=True)],
    text: Annotated[str, Body(embed=True, min_length=1, max_length=100)],
    opacity: Annotated[float, Body(embed=True, ge=0.05, le=1.0)] = 0.3,
    rotation: Annotated[float, Body(embed=True, ge=0.0, le=360.0)] = 45.0,
    font_size: Annotated[int, Body(embed=True, ge=8, le=144)] = 48,
    db: AsyncSession = Depends(get_db),
):
    """Añade marca de agua de texto a todas las páginas del PDF."""
    doc = await db.get(Document, doc_id)
    if not doc or doc.deleted_at:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    if doc.is_encrypted:
        raise HTTPException(status_code=422, detail="El documento está cifrado.")

    in_path = Path(doc.original_path)
    if not in_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco.")

    op = Operation(
        doc_id=doc_id,
        operation_type=OperationType.watermark,
        input_paths=[str(in_path)],
        params_json={"text": text, "opacity": opacity, "rotation": rotation, "font_size": font_size},
        status=OperationStatus.running,
    )
    db.add(op)
    await db.flush()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = settings.outputs_dir / str(op.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"watermarked_{ts}.pdf"

    try:
        add_text_watermark(in_path, out_path, text, opacity, rotation, font_size)
        out_hash = sha256_file(out_path)

        op.status = OperationStatus.success
        op.output_path = str(out_path)
        op.output_sha256 = out_hash
        op.completed_at = datetime.now(timezone.utc)

        append_event(
            event_type="WATERMARK_COMPLETED",
            doc_id=str(doc_id), operation_id=str(op.id),
            details={"text": text, "opacity": opacity},
            sha256_before=doc.sha256, sha256_after=out_hash,
            ip_address=request.client.host if request.client else None,
        )
    except Exception as e:
        op.status = OperationStatus.failed
        op.error_message = str(e)
        op.completed_at = datetime.now(timezone.utc)
        raise HTTPException(status_code=500, detail=f"Error al añadir watermark: {e}")

    return op


@router.get("/{operation_id}/download")
async def download_watermarked(operation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    op = await db.get(Operation, operation_id)
    if not op or op.operation_type != OperationType.watermark:
        raise HTTPException(status_code=404, detail="Operación no encontrada.")
    if op.status != OperationStatus.success:
        raise HTTPException(status_code=400, detail=f"Estado: {op.status}")
    path = Path(op.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(path=str(path), filename=path.name, media_type="application/pdf")
