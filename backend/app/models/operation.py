"""Modelo Operation — cada transformación PDF ejecutada."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, JSON, Enum as SAEnum, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OperationType(str, enum.Enum):
    merge = "merge"
    split = "split"
    compress = "compress"
    convert = "convert"
    watermark = "watermark"
    redact = "redact"
    ocr = "ocr"
    rotate = "rotate"
    reorder = "reorder"
    sign = "sign"


class OperationStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    doc_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    operation_type: Mapped[OperationType] = mapped_column(
        SAEnum(OperationType), nullable=False
    )
    input_paths: Mapped[list | None] = mapped_column(JSON)   # lista de rutas
    output_path: Mapped[str | None] = mapped_column(String(1024))
    output_sha256: Mapped[str | None] = mapped_column(String(64))
    params_json: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[OperationStatus] = mapped_column(
        SAEnum(OperationStatus), default=OperationStatus.pending
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
