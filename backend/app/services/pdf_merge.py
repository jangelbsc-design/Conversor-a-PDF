"""Servicio de merge: combina N PDFs en uno. Preserva originales."""
from pathlib import Path

import pikepdf


def merge_pdfs(input_paths: list[Path], output_path: Path) -> None:
    """
    Combina múltiples PDFs en un único archivo de salida.

    Los archivos de entrada son inmutables (solo lectura).
    El resultado se escribe en output_path (archivo versionado nuevo).

    Args:
        input_paths: Lista ordenada de rutas de PDF a combinar.
        output_path: Ruta de destino del PDF combinado.

    Raises:
        FileNotFoundError: Si algún archivo de entrada no existe.
        pikepdf.PdfError: Si algún PDF está dañado o cifrado.
        ValueError: Si la lista de rutas está vacía.
    """
    if not input_paths:
        raise ValueError("Se requiere al menos un PDF para combinar.")

    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf_out = pikepdf.Pdf.new()
    with pdf_out.open_metadata() as meta:
        meta["dc:creator"] = ["PDF Suite Local"]
        meta["xmp:CreatorTool"] = "PDF Suite Local — merge"

    for path in input_paths:
        with pikepdf.open(path, allow_overwriting_input=False) as pdf_in:
            pdf_out.pages.extend(pdf_in.pages)

    pdf_out.save(output_path, compress_streams=True)
