"""Servicio de rotación de páginas PDF."""
from pathlib import Path

import pikepdf

VALID_ANGLES = {0, 90, 180, 270}


def rotate_pages(
    input_path: Path,
    output_path: Path,
    rotations: dict[int, int],
) -> None:
    """
    Rota páginas específicas de un PDF.

    Args:
        input_path: PDF original (inmutable).
        output_path: PDF con rotaciones aplicadas.
        rotations: Diccionario {número_de_página_1indexed: ángulo_en_grados}.
                   Ej: {1: 90, 3: 180} rota la pág 1 y la pág 3.
                   Ángulos válidos: 0, 90, 180, 270.

    Raises:
        ValueError: Si algún ángulo o número de página es inválido.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")

    for angle in rotations.values():
        if angle not in VALID_ANGLES:
            raise ValueError(f"Ángulo inválido: {angle}. Usa 0, 90, 180 o 270.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
        total = len(pdf.pages)
        for page_num, angle in rotations.items():
            if page_num < 1 or page_num > total:
                raise ValueError(
                    f"Página {page_num} fuera de rango (1-{total})."
                )
            page = pdf.pages[page_num - 1]
            # Sumar ángulo actual al nuevo (módulo 360)
            current = int(page.get("/Rotate", 0))
            page["/Rotate"] = (current + angle) % 360

        pdf.save(output_path, compress_streams=True)


def rotate_all_pages(
    input_path: Path,
    output_path: Path,
    angle: int,
) -> None:
    """Rota todas las páginas el mismo ángulo."""
    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
        total = len(pdf.pages)
    rotations = {i: angle for i in range(1, total + 1)}
    rotate_pages(input_path, output_path, rotations)
