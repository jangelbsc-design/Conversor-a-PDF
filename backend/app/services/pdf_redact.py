"""
Servicio de redacción (redact): ennegrece regiones en un PDF.

⚠️ ADVERTENCIA: Esta redacción añade rectángulos negros sobre el contenido.
El texto subyacente puede seguir presente en el PDF si no se aplana
el documento correctamente. Para redacción legal certificada, usa
herramientas especializadas (Adobe Acrobat Pro, etc.).
"""
from pathlib import Path
from typing import NamedTuple

import pikepdf
from pikepdf import Dictionary, Name


class RedactRegion(NamedTuple):
    page: int       # 1-indexed
    x: float        # coordenada x desde la esquina inferior izquierda (puntos PDF)
    y: float        # coordenada y desde la esquina inferior izquierda (puntos PDF)
    width: float
    height: float


def redact_regions(
    input_path: Path,
    output_path: Path,
    regions: list[RedactRegion],
) -> None:
    """
    Aplica rectángulos negros opacos sobre las regiones especificadas.

    Nota: Esta operación añade un overlay opaco. El texto original
    permanece en el stream de contenido si el PDF no se aplana externamente.
    Esta limitación se muestra como advertencia en la UI.

    Args:
        input_path: PDF original (inmutable).
        output_path: PDF con redacciones aplicadas.
        regions: Lista de regiones a redactar por página.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")
    if not regions:
        raise ValueError("Se requiere al menos una región para redactar.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Agrupar por página
    by_page: dict[int, list[RedactRegion]] = {}
    for r in regions:
        by_page.setdefault(r.page, []).append(r)

    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
        total_pages = len(pdf.pages)

        for page_num, rects in by_page.items():
            if page_num < 1 or page_num > total_pages:
                raise ValueError(
                    f"Página {page_num} fuera de rango (1-{total_pages})."
                )
            page = pdf.pages[page_num - 1]

            # Construir stream de redacción
            lines = ["q", "0 g", "0 G"]  # color negro
            for r in rects:
                if r.width <= 0 or r.height <= 0:
                    continue
                lines.append(f"{r.x:.2f} {r.y:.2f} {r.width:.2f} {r.height:.2f} re")
                lines.append("f")  # fill (relleno)
            lines.append("Q")

            redact_stream = "\n".join(lines).encode("latin-1")
            rs = pdf.make_stream(redact_stream)

            existing = page.obj.get("/Contents")
            if existing is None:
                page.obj["/Contents"] = rs
            elif isinstance(existing, pikepdf.Array):
                existing.append(rs)
            else:
                page.obj["/Contents"] = pikepdf.Array([existing, rs])

        pdf.save(output_path, compress_streams=True)
