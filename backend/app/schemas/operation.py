"""Schemas Pydantic para Operations."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.operation import OperationStatus, OperationType


class OperationResponse(BaseModel):
    id: uuid.UUID
    doc_id: uuid.UUID | None
    operation_type: OperationType
    status: OperationStatus
    output_path: str | None
    output_sha256: str | None
    params_json: dict | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class DownloadResponse(BaseModel):
    operation_id: uuid.UUID
    download_url: str
    filename: str
    sha256: str
    size_bytes: int
