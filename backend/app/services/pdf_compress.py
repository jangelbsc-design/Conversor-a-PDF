"""Servicio de compresión PDF con pikepdf."""
from pathlib import Path

import pikepdf

# Niveles de compresión disponibles
COMPRESSION_PROFILES = {
    1: {
        "description": "Ligera — preserva calidad máxima",
        "compress_streams": True,
        "recompress_flate": False,
        "normalize_content": False,
    },
    2: {
        "description": "Media — balance calidad/tamaño",
        "compress_streams": True,
        "recompress_flate": True,
        "flate_level": 6,
        "normalize_content": True,
    },
    3: {
        "description": "Agresiva — máxima reducción de tamaño",
        "compress_streams": True,
        "recompress_flate": True,
        "flate_level": 9,
        "normalize_content": True,
        "object_stream_mode": pikepdf.ObjectStreamMode.generate,
    },
}


def compress_pdf(
    input_path: Path,
    output_path: Path,
    level: int = 2,
) -> dict:
    """
    Comprime un PDF preservando el original.

    Args:
        input_path: Ruta del PDF original (inmutable).
        output_path: Ruta del PDF comprimido (nuevo archivo versionado).
        level: Nivel de compresión 1 (ligera) a 3 (agresiva).

    Returns:
        Dict con size_before, size_after y ratio de compresión.

    Raises:
        ValueError: Si el nivel es inválido.
        FileNotFoundError: Si el archivo de entrada no existe.
    """
    if level not in COMPRESSION_PROFILES:
        raise ValueError(f"Nivel de compresión inválido: {level}. Usa 1, 2 o 3.")
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")

    profile = COMPRESSION_PROFILES[level].copy()
    description = profile.pop("description")

    size_before = input_path.stat().st_size
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
        pdf.save(output_path, **profile)

    size_after = output_path.stat().st_size
    ratio = round((1 - size_after / size_before) * 100, 1) if size_before > 0 else 0.0

    return {
        "size_before_bytes": size_before,
        "size_after_bytes": size_after,
        "reduction_percent": ratio,
        "profile": description,
    }
