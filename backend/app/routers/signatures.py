"""Router de signatures."""
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
from app.models.signature import SignatureRequest
from app.schemas.signature import (
    SignatureRequestCreate,
    SignatureRequestResponse,
    ConsentRecord,
)
from app.services.pdf_signature import place_signature_fields, record_consent_and_seal
from app.utils.event_log import append_event
from app.utils.hashing import sha256_file

router = APIRouter()

CONSENT_DEFAULT_TEXT = (
    "Confirmo que he revisado el documento y acepto firmarlo. "
    "AVISO: Este proceso NO constituye una firma electrónica cualificada o avanzada. "
    "No tiene validez legal equivalente a una firma certificada (eIDAS, ESIGN Act). "
    "Es un registro de consentimiento personal de bajo riesgo."
)


@router.post("/", response_model=SignatureRequestResponse, status_code=201)
async def create_signature_request(
    request: Request,
    payload: SignatureRequestCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una solicitud de firma: coloca campos visuales en el PDF.
    ⚠️ NO es una firma electrónica cualificada.
    """
    doc = await db.get(Document, payload.doc_id)
    if not doc or doc.deleted_at:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    if doc.is_encrypted:
        raise HTTPException(status_code=422, detail="El documento está cifrado.")

    in_path = Path(doc.original_path)
    sig_request = SignatureRequest(
        doc_id=payload.doc_id,
        signer_name=payload.signer_name,
        signer_email_local=payload.signer_email_local,
        field_positions_json=[f.model_dump() for f in payload.field_positions],
        consent_text=payload.consent_text or CONSENT_DEFAULT_TEXT,
    )
    db.add(sig_request)
    await db.flush()

    # Generar PDF con campos de firma visuales
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = settings.outputs_dir / f"sig_{sig_request.id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    fields_path = out_dir / f"with_fields_{ts}.pdf"

    try:
        place_signature_fields(in_path, fields_path, sig_request.field_positions_json)
        sig_request.output_path = str(fields_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error colocando campos: {e}")

    append_event(
        event_type="SIGNATURE_REQUEST_CREATED",
        doc_id=str(payload.doc_id),
        details={"signer_name": payload.signer_name, "fields": len(payload.field_positions)},
        sha256_before=doc.sha256,
        ip_address=request.client.host if request.client else None,
    )

    return sig_request


@router.post("/{sig_id}/consent", response_model=SignatureRequestResponse)
async def record_consent(
    sig_id: uuid.UUID,
    request: Request,
    payload: ConsentRecord,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra el consentimiento del firmante y sella el PDF con hash final.
    ⚠️ NO produce firma electrónica cualificada.
    """
    if not payload.consent_acknowledged:
        raise HTTPException(
            status_code=422,
            detail="Debes confirmar que entiendes las limitaciones de este proceso.",
        )

    sig_req = await db.get(SignatureRequest, sig_id)
    if not sig_req:
        raise HTTPException(status_code=404, detail="Solicitud de firma no encontrada.")
    if sig_req.sealed_at:
        raise HTTPException(status_code=409, detail="Este documento ya fue sellado.")

    fields_path = Path(sig_req.output_path)
    if not fields_path.exists():
        raise HTTPException(status_code=404, detail="Archivo con campos no encontrado.")

    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = fields_path.parent
    sealed_path = out_dir / f"sealed_{ts_str}.pdf"

    ip = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "")

    try:
        seal_result = record_consent_and_seal(
            signed_path=fields_path,
            output_path=sealed_path,
            signer_name=payload.signer_name_confirmation,
            consent_text=sig_req.consent_text or CONSENT_DEFAULT_TEXT,
            ip_address=ip,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sellando PDF: {e}")

    sig_req.consent_recorded_at = datetime.now(timezone.utc)
    sig_req.consent_ip_local = ip
    sig_req.consent_user_agent = ua
    sig_req.final_hash = seal_result["final_hash"]
    sig_req.output_path = str(sealed_path)
    sig_req.sealed_at = datetime.now(timezone.utc)

    append_event(
        event_type="SIGNATURE_SEALED",
        doc_id=str(sig_req.doc_id),
        details={
            "signer_name": payload.signer_name_confirmation,
            "sealed_at": seal_result["sealed_at"],
            "disclaimer": "NOT_A_QUALIFIED_SIGNATURE",
        },
        sha256_after=seal_result["final_hash"],
        ip_address=ip,
    )

    return sig_req


@router.get("/{sig_id}/download")
async def download_signed(sig_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    sig_req = await db.get(SignatureRequest, sig_id)
    if not sig_req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if not sig_req.sealed_at:
        raise HTTPException(status_code=400, detail="El documento aún no ha sido sellado.")
    path = Path(sig_req.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo sellado no encontrado.")
    return FileResponse(path=str(path), filename=path.name, media_type="application/pdf")
