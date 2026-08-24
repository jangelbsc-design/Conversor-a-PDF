"""Router de backup: exporta el store completo como ZIP."""
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import settings

router = APIRouter()


@router.get("/download")
async def download_backup():
    """
    Genera un ZIP del store completo (originales + outputs + audit.jsonl).
    El ZIP se crea en memoria y se transmite como streaming response.
    Ningún dato se sube a ningún servidor externo.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_filename = f"pdf_suite_backup_{ts}.zip"

    def generate_zip():
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            store = settings.store_path

            # Originales
            for f in (store / "originals").rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(store))

            # Outputs
            for f in (store / "outputs").rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(store))

            # Audit log
            audit_log = store / "audit.jsonl"
            if audit_log.exists():
                zf.write(audit_log, "audit.jsonl")

        buffer.seek(0)
        yield buffer.read()

    return StreamingResponse(
        generate_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
    )


@router.get("/stats")
async def backup_stats():
    """Retorna estadísticas del store local."""
    store = settings.store_path

    def dir_size(path: Path) -> int:
        return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

    originals_size = dir_size(store / "originals")
    outputs_size = dir_size(store / "outputs")
    audit_size = (store / "audit.jsonl").stat().st_size if (store / "audit.jsonl").exists() else 0

    return {
        "store_path": str(store),
        "originals_size_bytes": originals_size,
        "outputs_size_bytes": outputs_size,
        "audit_log_size_bytes": audit_size,
        "total_size_bytes": originals_size + outputs_size + audit_size,
        "originals_count": sum(1 for _ in (store / "originals").rglob("*") if _.is_file()),
        "outputs_count": sum(1 for _ in (store / "outputs").rglob("*") if _.is_file()),
    }
