"""Router de rotación de páginas."""
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
from app.services.pdf_rotate import rotate_pages, rotate_all_pages
from app.utils.event_log import append_event
from app.utils.hashing import sha256_file

router = APIRouter()


@router.post("/", response_model=OperationResponse)
async def rotate_document_pages(
    request: Request,
    doc_id: Annotated[uuid.UUID, Body(embed=True)],
    rotations: Annotated[dict[str, int] | None, Body(embed=True)] = None,
    rotate_all: Annotated[int | None, Body(embed=True)] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Rota páginas de un PDF.
    - rotations: {"1": 90, "3": 180} → rota páginas específicas.
    - rotate_all: 90 → rota todas las páginas ese ángulo.
    """
    doc = await db.get(Document, doc_id)
    if not doc or doc.deleted_at:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    if doc.is_encrypted:
        raise HTTPException(status_code=422, detail="El documento está cifrado.")

    in_path = Path(doc.original_path)
    if not in_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco.")

    if not rotations and rotate_all is None:
        raise HTTPException(status_code=422, detail="Especifica 'rotations' o 'rotate_all'.")

    op = Operation(
        doc_id=doc_id,
        operation_type=OperationType.rotate,
        input_paths=[str(in_path)],
        params_json={"rotations": rotations, "rotate_all": rotate_all},
        status=OperationStatus.running,
    )
    db.add(op)
    await db.flush()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = settings.outputs_dir / str(op.id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"rotated_{ts}.pdf"

    try:
        if rotate_all is not None:
            rotate_all_pages(in_path, out_path, angle=rotate_all)
        else:
            rot_dict = {int(k): v for k, v in rotations.items()}
            rotate_pages(in_path, out_path, rot_dict)

        out_hash = sha256_file(out_path)
        op.status = OperationStatus.success
        op.output_path = str(out_path)
        op.output_sha256 = out_hash
        op.completed_at = datetime.now(timezone.utc)

        append_event(
            event_type="ROTATE_COMPLETED",
            doc_id=str(doc_id), operation_id=str(op.id),
            details={"rotations": rotations, "rotate_all": rotate_all},
            sha256_before=doc.sha256, sha256_after=out_hash,
            ip_address=request.client.host if request.client else None,
        )
    except Exception as e:
        op.status = OperationStatus.failed
        op.error_message = str(e)
        op.completed_at = datetime.now(timezone.utc)
        raise HTTPException(status_code=500, detail=f"Error al rotar: {e}")

    return op


@router.get("/{operation_id}/download")
async def download_rotated(operation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    op = await db.get(Operation, operation_id)
    if not op or op.operation_type != OperationType.rotate:
        raise HTTPException(status_code=404, detail="Operación no encontrada.")
    if op.status != OperationStatus.success:
        raise HTTPException(status_code=400, detail=f"Estado: {op.status}")
    path = Path(op.output_path)
    return FileResponse(path=str(path), filename=path.name, media_type="application/pdf")
