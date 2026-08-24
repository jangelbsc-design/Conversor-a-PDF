"""Utilidades de hashing SHA-256."""
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Calcula SHA-256 de un archivo en streaming (seguro para archivos grandes)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Calcula SHA-256 de bytes en memoria."""
    return hashlib.sha256(data).hexdigest()
