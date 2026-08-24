"""Migración inicial: crea todas las tablas de la aplicación.

Revision ID: 001
Revises: 
Create Date: 2026-08-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── documents ──────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename_safe", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("original_path", sa.String(1024), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_forms", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_signatures", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("warnings_json", sa.String(4096), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_created_at", "documents", ["created_at"])
    op.create_index("ix_documents_deleted_at", "documents", ["deleted_at"])

    # ── operations ─────────────────────────────────────────────────
    op.create_table(
        "operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "operation_type",
            sa.Enum("merge","split","compress","convert","watermark","redact","ocr","rotate","reorder","sign",
                    name="operationtype"),
            nullable=False,
        ),
        sa.Column("input_paths", postgresql.JSON(), nullable=True),
        sa.Column("output_path", sa.String(1024), nullable=True),
        sa.Column("output_sha256", sa.String(64), nullable=True),
        sa.Column("params_json", postgresql.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending","running","success","failed", name="operationstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operations_doc_id", "operations", ["doc_id"])
    op.create_index("ix_operations_created_at", "operations", ["created_at"])

    # ── audit_events (append-only) ─────────────────────────────────
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("doc_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details_json", postgresql.JSON(), nullable=True),
        sa.Column("sha256_before", sa.String(64), nullable=True),
        sa.Column("sha256_after", sa.String(64), nullable=True),
        sa.Column("actor", sa.String(255), nullable=False, server_default="local_user"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_doc_id", "audit_events", ["doc_id"])
    # No permitir UPDATE ni DELETE en audit_events — aplicar vía RLS si se desea

    # ── signature_requests ─────────────────────────────────────────
    op.create_table(
        "signature_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("doc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signer_name", sa.String(255), nullable=True),
        sa.Column("signer_email_local", sa.String(255), nullable=True),
        sa.Column("field_positions_json", postgresql.JSON(), nullable=True),
        sa.Column("consent_text", sa.Text(), nullable=True),
        sa.Column("consent_recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_ip_local", sa.String(45), nullable=True),
        sa.Column("consent_user_agent", sa.String(512), nullable=True),
        sa.Column("final_hash", sa.String(64), nullable=True),
        sa.Column("output_path", sa.String(1024), nullable=True),
        sa.Column("sealed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signature_requests_doc_id", "signature_requests", ["doc_id"])


def downgrade() -> None:
    op.drop_table("signature_requests")
    op.drop_table("audit_events")
    op.drop_table("operations")
    op.drop_table("documents")
    op.execute("DROP TYPE IF EXISTS operationtype")
    op.execute("DROP TYPE IF EXISTS operationstatus")
