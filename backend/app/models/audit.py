"""Modelo AuditEvent — log append-only (sin UPDATE ni DELETE permitidos)."""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    doc_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    operation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True
    )
    details_json: Mapped[dict | None] = mapped_column(JSON)
    sha256_before: Mapped[str | None] = mapped_column(String(64))
    sha256_after: Mapped[str | None] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(255), default="local_user")
    ip_address: Mapped[str | None] = mapped_column(String(45))
    # timestamp es inmutable — nunca se actualiza
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
