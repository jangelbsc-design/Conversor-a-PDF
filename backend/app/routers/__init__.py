"""Exports de todos los routers."""
from app.routers import (
    documents, merge, split, compress, convert,
    watermark, redact, ocr, rotate, reorder,
    preview, signatures, audit, backup,
)

__all__ = [
    "documents", "merge", "split", "compress", "convert",
    "watermark", "redact", "ocr", "rotate", "reorder",
    "preview", "signatures", "audit", "backup",
]
