"""Servicio de marca de agua (watermark) con texto o imagen."""
import math
from pathlib import Path

import pikepdf
from pikepdf import Array, Dictionary, Name


def add_text_watermark(
    input_path: Path,
    output_path: Path,
    text: str,
    opacity: float = 0.3,
    rotation_deg: float = 45.0,
    font_size: int = 48,
) -> None:
    """
    Añade una marca de agua de texto diagonal a todas las páginas.

    Usa Helvetica (Type1 estándar, disponible en todos los visores PDF).

    Args:
        input_path: PDF original (inmutable).
        output_path: PDF con watermark (nuevo archivo).
        text: Texto del watermark.
        opacity: Opacidad del texto (0.0 = invisible, 1.0 = sólido).
        rotation_deg: Ángulo de rotación en grados.
        font_size: Tamaño de fuente en puntos.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("opacity debe estar entre 0.0 y 1.0")
    # Sanear texto para PDF (escapar paréntesis)
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    angle_rad = math.radians(rotation_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
        font_ref = pdf.make_indirect(
            Dictionary(
                Type=Name("/Font"),
                Subtype=Name("/Type1"),
                BaseFont=Name("/Helvetica"),
                Encoding=Name("/WinAnsiEncoding"),
            )
        )

        for page in pdf.pages:
            mb = page.mediabox
            width = float(mb[2]) - float(mb[0])
            height = float(mb[3]) - float(mb[1])
            cx = width / 2.0
            cy = height / 2.0

            # Stream de contenido: texto centrado y rotado
            wm_stream = (
                f"q\n"
                f"{opacity:.4f} g\n"                          # color gris con opacidad
                f"{opacity:.4f} G\n"
                f"BT\n"
                f"/WMFont {font_size} Tf\n"
                f"{cos_a:.4f} {sin_a:.4f} {-sin_a:.4f} {cos_a:.4f} {cx:.2f} {cy:.2f} Tm\n"
                f"({safe_text}) Tj\n"
                f"ET\n"
                f"Q\n"
            ).encode("latin-1")

            # Añadir fuente a los recursos de la página
            page_res = page.obj.get("/Resources", Dictionary())
            if "/Font" not in page_res:
                page_res["/Font"] = Dictionary()
            page_res["/Font"]["/WMFont"] = font_ref
            page.obj["/Resources"] = page_res

            # Añadir watermark stream DESPUÉS del contenido existente
            wm = pdf.make_stream(wm_stream)
            existing = page.obj.get("/Contents")
            if existing is None:
                page.obj["/Contents"] = wm
            elif isinstance(existing, pikepdf.Array):
                existing.append(wm)
            else:
                page.obj["/Contents"] = pikepdf.Array([existing, wm])

        pdf.save(output_path, compress_streams=True)
