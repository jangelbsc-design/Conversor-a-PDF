"""Servicio de previews: genera miniaturas PNG de cada página."""
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image


def generate_page_previews(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 72,
    max_width: int = 400,
    page_numbers: list[int] | None = None,
) -> list[Path]:
    """
    Genera imágenes PNG de páginas del PDF.

    Args:
        pdf_path: Ruta del PDF.
        output_dir: Directorio de salida para los PNGs.
        dpi: Resolución de renderizado (72 para preview, 150 para mayor calidad).
        max_width: Ancho máximo de la miniatura en píxeles.
        page_numbers: Lista de páginas a renderizar (1-indexed). None = todas.

    Returns:
        Lista de rutas PNG generadas.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    kwargs: dict = {
        "pdf_path": str(pdf_path),
        "dpi": dpi,
        "fmt": "PNG",
        "thread_count": 2,
    }
    if page_numbers:
        kwargs["first_page"] = min(page_numbers)
        kwargs["last_page"] = max(page_numbers)

    images: list[Image.Image] = convert_from_path(**kwargs)

    preview_paths: list[Path] = []
    for i, img in enumerate(images):
        # Calcular número de página real
        base_page = (page_numbers[0] if page_numbers else 1) + i

        # Redimensionar preservando ratio
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        out_path = output_dir / f"page_{base_page:04d}.png"
        img.save(out_path, "PNG", optimize=True)
        preview_paths.append(out_path)

    return preview_paths


def get_page_count(pdf_path: Path) -> int:
    """Retorna el número de páginas de un PDF sin renderizarlo."""
    import pikepdf
    with pikepdf.open(pdf_path) as pdf:
        return len(pdf.pages)
