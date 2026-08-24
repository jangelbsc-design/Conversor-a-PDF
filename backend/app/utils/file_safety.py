"""Utilidades de seguridad para nombres de archivos y validación MIME."""
import re
import unicodedata
from pathlib import Path

import magic

# Tipos MIME permitidos para subida directa
ALLOWED_PDF_MIME = {"application/pdf"}
ALLOWED_OFFICE_MIME = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",        # .xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",# .pptx
    "application/msword",                                                         # .doc
    "application/vnd.ms-excel",                                                   # .xls
    "application/vnd.ms-powerpoint",                                              # .ppt
    "application/vnd.oasis.opendocument.text",                                    # .odt
    "application/vnd.oasis.opendocument.spreadsheet",                             # .ods
    "application/vnd.oasis.opendocument.presentation",                            # .odp
    "application/rtf",                                                             # .rtf
    "text/rtf",                                                                    # .rtf (libmagic en Windows)
    "text/plain",                                                                  # .txt
}
ALLOWED_MIME_TYPES = ALLOWED_PDF_MIME | ALLOWED_OFFICE_MIME

# Extensiones permitidas
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls",
    ".pptx", ".ppt", ".odt", ".ods", ".odp", ".rtf", ".txt",
}

_UNSAFE_CHARS = re.compile(r"[^\w\-.]")
_MULTIPLE_DOTS = re.compile(r"\.{2,}")
_LEADING_DOTS_DASHES = re.compile(r"^[.\-]+")


def safe_filename(name: str, max_length: int = 200) -> str:
    """
    Normaliza un nombre de archivo:
    - Elimina caracteres Unicode peligrosos
    - Elimina secuencias de puntos dobles (..)
    - Limita longitud
    - Preserva extensión
    """
    # Normalizar Unicode NFC
    name = unicodedata.normalize("NFC", name)
    # Separar stem y extensión
    path = Path(name)
    stem = path.stem
    suffix = path.suffix.lower()

    # Reemplazar caracteres no seguros por guión bajo
    stem = _UNSAFE_CHARS.sub("_", stem)
    stem = _LEADING_DOTS_DASHES.sub("", stem)
    stem = _MULTIPLE_DOTS.sub(".", stem)
    stem = stem[:max_length] or "file"

    return f"{stem}{suffix}"


def validate_mime_type(file_bytes: bytes, expected_extension: str) -> str:
    """
    Detecta el MIME type real del contenido (no solo la extensión).
    Lanza ValueError si no está permitido.
    """
    detected = magic.from_buffer(file_bytes[:8192], mime=True)
    if detected not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Tipo de archivo no permitido: {detected}. "
            f"Se aceptan: PDF y documentos Office."
        )
    return detected


def validate_extension(filename: str) -> str:
    """Valida que la extensión esté en la lista blanca."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Extensión '{ext}' no permitida. "
            f"Permitidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext
