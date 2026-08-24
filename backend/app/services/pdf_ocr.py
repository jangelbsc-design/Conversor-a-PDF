"""Servicio OCR: añade capa de texto a PDFs escaneados con ocrmypdf + tesseract."""
from pathlib import Path


def _get_ocrmypdf():
    try:
        import ocrmypdf
        return ocrmypdf
    except ImportError as e:
        raise RuntimeError(
            "OCR no disponible en este entorno: falta el paquete 'ocrmypdf' "
            "(y requiere Tesseract + Ghostscript instalados)."
        ) from e


def run_ocr(
    input_path: Path,
    output_path: Path,
    language: str = "spa",
    deskew: bool = True,
    skip_text: bool = False,
) -> dict:
    """
    Aplica OCR al PDF usando ocrmypdf (tesseract como motor).

    Args:
        input_path: PDF original (inmutable).
        output_path: PDF con capa de texto OCR añadida.
        language: Idioma tesseract (ej: "spa+eng", "eng", "spa").
        deskew: Corregir inclinación automáticamente.
        skip_text: Si True, aplica OCR solo a páginas sin texto existente.

    Returns:
        Dict con resultado de la operación.

    Raises:
        FileNotFoundError: Si el PDF de entrada no existe.
        ocrmypdf.exceptions.PriorOcrFoundError: Si skip_text=False y ya hay texto.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    kwargs: dict = {
        "input_file": input_path,
        "output_file": output_path,
        "language": language,
        "deskew": deskew,
        "progress_bar": False,
        "jobs": 2,
    }

    if skip_text:
        kwargs["skip_text"] = True
    else:
        kwargs["force_ocr"] = False
        kwargs["redo_ocr"] = False

    try:
        ocr_mod = _get_ocrmypdf()
        result = ocr_mod.ocr(**kwargs)
        return {
            "status": "success",
            "language": language,
            "deskew_applied": deskew,
        }
    except RuntimeError:
        raise
    except Exception as e:
        import ocrmypdf
        if not isinstance(e, ocrmypdf.exceptions.PriorOcrFoundError):
            raise
        # Ya tiene texto — reintentamos con skip_text
        kwargs["skip_text"] = True
        kwargs.pop("force_ocr", None)
        kwargs.pop("redo_ocr", None)
        ocr_mod.ocr(**kwargs)
        return {
            "status": "success_skip_text",
            "language": language,
            "warning": "El PDF ya tenía texto. Se aplicó OCR solo a páginas sin texto.",
        }
