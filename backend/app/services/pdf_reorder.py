"""Servicio de reordenamiento de páginas PDF."""
from pathlib import Path

import pikepdf


def reorder_pages(
    input_path: Path,
    output_path: Path,
    new_order: list[int],
) -> None:
    """
    Reordena las páginas de un PDF según el orden especificado.

    Args:
        input_path: PDF original (inmutable).
        output_path: PDF con páginas reordenadas.
        new_order: Lista de números de página 1-indexed en el nuevo orden.
                   Ej: [3, 1, 2] mueve la pág 3 al inicio.
                   Puede contener duplicados para repetir páginas.

    Raises:
        ValueError: Si el orden contiene páginas fuera de rango.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
    if not new_order:
        raise ValueError("new_order no puede estar vacío.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
        total = len(pdf.pages)

        for page_num in new_order:
            if page_num < 1 or page_num > total:
                raise ValueError(
                    f"Página {page_num} fuera de rango (1-{total})."
                )

        pdf_out = pikepdf.Pdf.new()
        for page_num in new_order:
            pdf_out.pages.append(pdf.pages[page_num - 1])

        pdf_out.save(output_path, compress_streams=True)
