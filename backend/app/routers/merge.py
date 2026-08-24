"""Router de merge: combina múltiples PDFs."""
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
from app.services.pdf_merge import merge_pdfs
from app.utils.event_log import append_event
from app.utils.hashing import sha256_file

router = APIRouter()


@router.post("/", response_model=OperationResponse)
async def merge_documents(
    request: Request,
    doc_ids: Annotated[list[uuid.UUID], Body(embed=True, min_length=2)],
    db: AsyncSession = Depends(get_db),
):
    """
    Combina 2 o más PDFs en un único archivo.
    Los originales permanecen intactos.
    """
    # Resolver rutas de los documentos
    input_paths: list[Path] = []
    sha256s: list[str] = []
    for doc_id in doc_ids:
        doc = await db.get(Document, doc_id)
        if not doc or doc.deleted_at:
            raise HTTPException(status_code=404, detail=f"Documento {doc_id} no encontrado.")
        if doc.is_encrypted:
            raise HTTPException(status_code=422, detail=f"Documento {doc_id} está cifrado.")
        path = Path(doc.original_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Archivo no encontrado en disco: {doc_id}")
        input_paths.append(path)
        sha256s.append(doc.sha256)

    # Crear operación
    op = Operation(
        operation_type=OperationType.merge,
        input_paths=[str(p) for p in input_paths],
        params_json={"doc_ids": [str(d) for d in doc_ids]},
        status=OperationStatus.running,
    )
    db.add(op)
    await db.flush()

    # Nombre y ruta del output versionado
    op_id = op.id
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = settings.outputs_dir / str(op_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"merged_{ts}.pdf"

    try:
        merge_pdfs(input_paths, out_path)
        out_hash = sha256_file(out_path)

        op.status = OperationStatus.success
        op.output_path = str(out_path)
        op.output_sha256 = out_hash
        op.completed_at = datetime.now(timezone.utc)

        append_event(
            event_type="MERGE_COMPLETED",
            operation_id=str(op_id),
            details={"input_count": len(doc_ids), "output_path": str(out_path)},
            sha256_before=",".join(sha256s),
            sha256_after=out_hash,
            ip_address=request.client.host if request.client else None,
        )

    except Exception as e:
        op.status = OperationStatus.failed
        op.error_message = str(e)
        op.completed_at = datetime.now(timezone.utc)
        raise HTTPException(status_code=500, detail=f"Error al combinar PDFs: {e}")

    return op


@router.get("/{operation_id}/download")
async def download_merged(operation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    op = await db.get(Operation, operation_id)
    if not op or op.operation_type != OperationType.merge:
        raise HTTPException(status_code=404, detail="Operación no encontrada.")
    if op.status != OperationStatus.success:
        raise HTTPException(status_code=400, detail=f"Operación en estado: {op.status}")
    path = Path(op.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo de salida no encontrado.")
    return FileResponse(path=str(path), filename=path.name, media_type="application/pdf")
