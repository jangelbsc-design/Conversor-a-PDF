"""Modelo SignatureRequest — campos de firma, consentimiento y hash final."""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, JSON, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SignatureRequest(Base):
    __tablename__ = "signature_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    doc_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    signer_name: Mapped[str | None] = mapped_column(String(255))
    signer_email_local: Mapped[str | None] = mapped_column(String(255))

    # Posiciones de campos en el PDF (lista de {page, x, y, width, height, type})
    field_positions_json: Mapped[list | None] = mapped_column(JSON)

    # Texto de consentimiento mostrado al firmante
    consent_text: Mapped[str | None] = mapped_column(Text)

    # Registro de consentimiento
    consent_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_ip_local: Mapped[str | None] = mapped_column(String(45))
    consent_user_agent: Mapped[str | None] = mapped_column(String(512))

    # Sellado final (hash del PDF sellado)
    final_hash: Mapped[str | None] = mapped_column(String(64))
    output_path: Mapped[str | None] = mapped_column(String(1024))
    sealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ⚠️ AVISO: Este proceso NO produce una firma electrónica cualificada.
    # No cumple eIDAS, ESIGN Act ni ningún marco de firma legal regulado.
    # Es un registro de consentimiento local de bajo riesgo.
    DISCLAIMER: str = (
        "Este proceso NO constituye una firma electrónica cualificada o avanzada. "
        "No verificamos identidades, no usamos certificados cualificados y no cumplimos "
        "eIDAS ni ESIGN Act. Uso exclusivo personal y de bajo riesgo."
    )
