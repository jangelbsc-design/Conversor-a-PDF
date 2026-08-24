"""Schemas Pydantic para Document."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentWarning(BaseModel):
    type: str
    message: str
    severity: str = "warning"  # "info" | "warning" | "error"


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename_safe: str
    original_filename: str
    mime_type: str | None
    sha256: str
    size_bytes: int | None
    page_count: int | None
    is_encrypted: bool
    has_forms: bool
    has_signatures: bool
    warnings: list[DocumentWarning] = []
    created_at: datetime
    expires_at: datetime | None
    deleted_at: datetime | None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
