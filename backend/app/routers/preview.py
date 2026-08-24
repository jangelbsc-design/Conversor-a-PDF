"""Router de previews: genera miniaturas PNG de páginas."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document
from app.services.pdf_preview import generate_page_previews, get_page_count

router = APIRouter()


@router.get("/{doc_id}/pages")
async def list_page_previews(
    doc_id: uuid.UUID,
    dpi: int = Query(default=72, ge=36, le=150),
    max_width: int = Query(default=400, ge=100, le=1200),
    db: AsyncSession = Depends(get_db),
):
    """
    Genera y retorna metadatos de previews PNG de todas las páginas.
    Las imágenes se sirven desde /api/preview/{doc_id}/page/{page_num}.
    """
    doc = await db.get(Document, doc_id)
    if not doc or doc.deleted_at:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    in_path = Path(doc.original_path)
    if not in_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco.")

    preview_dir = settings.previews_dir / str(doc_id)
    preview_dir.mkdir(parents=True, exist_ok=True)

    try:
        preview_paths = generate_page_previews(in_path, preview_dir, dpi=dpi, max_width=max_width)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando previews: {e}")

    return {
        "doc_id": str(doc_id),
        "page_count": len(preview_paths),
        "pages": [
            {
                "page": i + 1,
                "preview_url": f"/api/preview/{doc_id}/page/{i + 1}",
            }
            for i in range(len(preview_paths))
        ],
    }


@router.get("/{doc_id}/page/{page_num}")
async def get_page_preview(
    doc_id: uuid.UUID,
    page_num: int,
    db: AsyncSession = Depends(get_db),
):
    """Sirve el PNG de una página específica."""
    doc = await db.get(Document, doc_id)
    if not doc or doc.deleted_at:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    preview_path = settings.previews_dir / str(doc_id) / f"page_{page_num:04d}.png"

    if not preview_path.exists():
        # Generar si no existe
        in_path = Path(doc.original_path)
        preview_dir = settings.previews_dir / str(doc_id)
        preview_dir.mkdir(parents=True, exist_ok=True)
        try:
            generate_page_previews(in_path, preview_dir, page_numbers=[page_num])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generando preview: {e}")

    if not preview_path.exists():
        raise HTTPException(status_code=404, detail=f"Preview de página {page_num} no disponible.")

    return FileResponse(path=str(preview_path), media_type="image/png")
