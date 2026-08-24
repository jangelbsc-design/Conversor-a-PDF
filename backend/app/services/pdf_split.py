"""Servicio de split: extrae rangos de páginas de un PDF."""
from pathlib import Path

import pikepdf


def split_pdf(
    input_path: Path,
    page_ranges: list[tuple[int, int]],
    output_dir: Path,
    base_name: str = "split",
) -> list[Path]:
    """
    Divide un PDF en múltiples archivos según rangos de páginas.

    Args:
        input_path: Ruta del PDF original (inmutable).
        page_ranges: Lista de (inicio, fin) con páginas 1-indexed, inclusive.
                     Ej: [(1, 3), (5, 7)] produce dos PDFs.
        output_dir: Directorio donde se guardan los PDFs resultantes.
        base_name: Prefijo del nombre de los archivos de salida.

    Returns:
        Lista de rutas de los PDFs generados.

    Raises:
        FileNotFoundError: Si el PDF de entrada no existe.
        ValueError: Si los rangos son inválidos.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
    if not page_ranges:
        raise ValueError("Se requiere al menos un rango de páginas.")

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf_in:
        total_pages = len(pdf_in.pages)

        for i, (start, end) in enumerate(page_ranges):
            # Validar rango
            if start < 1 or end < start or end > total_pages:
                raise ValueError(
                    f"Rango inválido ({start}-{end}). "
                    f"El PDF tiene {total_pages} páginas (1-indexed)."
                )

            pdf_out = pikepdf.Pdf.new()
            for page_idx in range(start - 1, end):  # 0-indexed internamente
                pdf_out.pages.append(pdf_in.pages[page_idx])

            out_path = output_dir / f"{base_name}_{i + 1:03d}_pags_{start}-{end}.pdf"
            pdf_out.save(out_path, compress_streams=True)
            outputs.append(out_path)

    return outputs


def split_by_pages(input_path: Path, output_dir: Path) -> list[Path]:
    """Divide el PDF en archivos de una sola página."""
    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf_in:
        total = len(pdf_in.pages)
    ranges = [(i, i) for i in range(1, total + 1)]
    return split_pdf(input_path, ranges, output_dir, base_name="pagina")
