"""Schemas Pydantic para SignatureRequests."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SignatureFieldPosition(BaseModel):
    page: int = Field(..., ge=1, description="Número de página (1-indexed)")
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    field_type: str = Field(default="signature", pattern="^(signature|initials|date)$")
    label: str | None = None


class SignatureRequestCreate(BaseModel):
    doc_id: uuid.UUID
    signer_name: str = Field(..., min_length=1, max_length=255)
    signer_email_local: str | None = None
    field_positions: list[SignatureFieldPosition] = Field(..., min_length=1)
    consent_text: str | None = None


class ConsentRecord(BaseModel):
    """Registro de consentimiento del firmante."""
    signature_request_id: uuid.UUID
    # ⚠️ NO es firma cualificada. Solo registro de consentimiento local.
    consent_acknowledged: bool = Field(
        ...,
        description="El firmante confirma que entiende que esto NO es una firma legal cualificada",
    )
    signer_name_confirmation: str


class SignatureRequestResponse(BaseModel):
    id: uuid.UUID
    doc_id: uuid.UUID
    signer_name: str | None
    field_positions_json: list | None
    consent_recorded_at: datetime | None
    final_hash: str | None
    output_path: str | None
    sealed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
