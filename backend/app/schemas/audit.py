"""Schemas Pydantic para AuditEvents."""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    doc_id: uuid.UUID | None
    operation_id: uuid.UUID | None
    details_json: dict | None
    sha256_before: str | None
    sha256_after: str | None
    actor: str
    ip_address: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    events: list[AuditEventResponse]
    total: int
