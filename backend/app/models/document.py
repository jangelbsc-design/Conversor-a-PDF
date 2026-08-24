"""Modelo Document — un archivo subido por el usuario."""
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, func, Boolean, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    filename_safe: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    original_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    has_forms: Mapped[bool] = mapped_column(Boolean, default=False)
    has_signatures: Mapped[bool] = mapped_column(Boolean, default=False)
    warnings_json: Mapped[str | None] = mapped_column(String(4096))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
