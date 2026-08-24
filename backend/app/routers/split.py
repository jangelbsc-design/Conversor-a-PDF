"""Router de split: divide un PDF por rangos de páginas."""
import uuid
import zipfile
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
from app.services.pdf_split import split_pdf, split_by_pages
from app.utils.event_log import append_event
from app.utils.hashing import sha256_file

router = APIRouter()


@router.post("/", response_model=OperationResponse)
async def split_document(
    request: Request,
    doc_id: Annotated[uuid.UUID, Body(embed=True)],
    page_ranges: Annotated[list[list[int]] | None, Body(embed=True)] = None,
    split_all: Annotated[bool, Body(embed=True)] = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Divide un PDF.

    - page_ranges: [[1,3],[5,7]] → dos PDFs con páginas 1-3 y 5-7.
    - split_all: True → un PDF por página.
    """
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
        operation_type=OperationType.split,
        input_paths=[str(in_path)],
        params_json={"page_ranges": page_ranges, "split_all": split_all},
        status=OperationStatus.running,
    )
    db.add(op)
    await db.flush()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = settings.outputs_dir / str(op.id)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if split_all:
            output_files = split_by_pages(in_path, out_dir)
        elif page_ranges:
            ranges = [(r[0], r[1]) for r in page_ranges]
            output_files = split_pdf(in_path, ranges, out_dir)
        else:
            raise ValueError("Especifica page_ranges o split_all=true.")

        # Empaquetar en ZIP si hay múltiples archivos
        if len(output_files) > 1:
            zip_path = out_dir / f"split_{ts}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in output_files:
                    zf.write(f, f.name)
            final_path = zip_path
            final_hash = sha256_file(zip_path)
        else:
            final_path = output_files[0]
            final_hash = sha256_file(final_path)

        op.status = OperationStatus.success
        op.output_path = str(final_path)
        op.output_sha256 = final_hash
        op.completed_at = datetime.now(timezone.utc)

        append_event(
            event_type="SPLIT_COMPLETED",
            doc_id=str(doc_id),
            operation_id=str(op.id),
            details={"files_created": len(output_files)},
            sha256_before=doc.sha256,
            sha256_after=final_hash,
            ip_address=request.client.host if request.client else None,
        )

    except Exception as e:
        op.status = OperationStatus.failed
        op.error_message = str(e)
        op.completed_at = datetime.now(timezone.utc)
        raise HTTPException(status_code=500, detail=f"Error al dividir PDF: {e}")

    return op


@router.get("/{operation_id}/download")
async def download_split(operation_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    op = await db.get(Operation, operation_id)
    if not op or op.operation_type != OperationType.split:
        raise HTTPException(status_code=404, detail="Operación no encontrada.")
    if op.status != OperationStatus.success:
        raise HTTPException(status_code=400, detail=f"Operación en estado: {op.status}")
    path = Path(op.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    media = "application/zip" if path.suffix == ".zip" else "application/pdf"
    return FileResponse(path=str(path), filename=path.name, media_type=media)
