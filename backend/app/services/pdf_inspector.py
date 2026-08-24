"""
Servicio de inspección PDF: detecta fuentes, formularios, firmas y cifrado.
Genera advertencias antes de ejecutar cualquier operación.
"""
from pathlib import Path
from typing import Any

import pikepdf


def inspect_pdf(pdf_path: Path) -> dict[str, Any]:
    """
    Analiza un PDF y devuelve metadatos y advertencias.

    Warnings retornados:
    - ENCRYPTION: PDF cifrado (bloquea operaciones)
    - FORMS: Formularios AcroForm (pueden perderse)
    - SIGNATURES: Firmas digitales (se invalidan con cualquier operación)
    - UNEMBEDDED_FONTS: Fuentes no embebidas (pueden sustituirse)
    - JAVASCRIPT: JavaScript en el PDF (posible vector de ataque)
    - XFA: Formularios XFA (no soportados por pikepdf)

    Returns:
        Dict con: page_count, is_encrypted, has_forms, has_signatures,
                  has_javascript, warnings (lista), metadata.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")

    result: dict[str, Any] = {
        "page_count": 0,
        "is_encrypted": False,
        "has_forms": False,
        "has_signatures": False,
        "has_javascript": False,
        "has_xfa": False,
        "unembedded_fonts": [],
        "warnings": [],
        "metadata": {},
    }

    # Verificar cifrado antes de abrir
    try:
        with pikepdf.open(pdf_path) as pdf:
            result["page_count"] = len(pdf.pages)

            # ── Cifrado ──────────────────────────────────────────────
            if pdf.is_encrypted:
                result["is_encrypted"] = True
                result["warnings"].append({
                    "type": "ENCRYPTION",
                    "severity": "error",
                    "message": "El PDF está cifrado. Introduce la contraseña para continuar.",
                })

            root = pdf.Root

            # ── Formularios AcroForm ─────────────────────────────────
            if "/AcroForm" in root:
                result["has_forms"] = True
                acroform = root["/AcroForm"]
                result["warnings"].append({
                    "type": "FORMS",
                    "severity": "warning",
                    "message": (
                        "El PDF contiene formularios AcroForm. "
                        "Algunas operaciones (compress, rotate) pueden alterar o eliminar los campos."
                    ),
                })
                # Detectar XFA
                if "/XFA" in acroform:
                    result["has_xfa"] = True
                    result["warnings"].append({
                        "type": "XFA",
                        "severity": "warning",
                        "message": "El PDF usa formularios XFA. No están soportados y serán ignorados.",
                    })

            # ── Firmas digitales ─────────────────────────────────────
            if "/AcroForm" in root:
                acroform = root["/AcroForm"]
                fields = acroform.get("/Fields", pikepdf.Array())
                for field_ref in fields:
                    try:
                        field = pdf.get_object(field_ref.objgen)
                        if field.get("/FT") == pikepdf.Name("/Sig"):
                            result["has_signatures"] = True
                            break
                    except Exception:
                        continue

            if result["has_signatures"]:
                result["warnings"].append({
                    "type": "SIGNATURES",
                    "severity": "warning",
                    "message": (
                        "El PDF contiene firmas digitales que serán invalidadas "
                        "por cualquier operación de modificación."
                    ),
                })

            # ── JavaScript ──────────────────────────────────────────
            if "/Names" in root:
                names = root["/Names"]
                if "/JavaScript" in names:
                    result["has_javascript"] = True
                    result["warnings"].append({
                        "type": "JAVASCRIPT",
                        "severity": "warning",
                        "message": "El PDF contiene JavaScript. Será eliminado en operaciones de salida.",
                    })

            # ── Fuentes no embebidas ─────────────────────────────────
            unembedded = _find_unembedded_fonts(pdf)
            result["unembedded_fonts"] = unembedded
            if unembedded:
                result["warnings"].append({
                    "type": "UNEMBEDDED_FONTS",
                    "severity": "info",
                    "message": (
                        f"Fuentes no embebidas detectadas: {', '.join(unembedded[:5])}. "
                        "El texto puede renderizarse de forma diferente en otros visores."
                    ),
                })

            # ── Metadatos ────────────────────────────────────────────
            try:
                with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                    result["metadata"] = dict(meta)
            except Exception:
                result["metadata"] = {}

    except pikepdf.PasswordError:
        result["is_encrypted"] = True
        result["warnings"].append({
            "type": "ENCRYPTION",
            "severity": "error",
            "message": "PDF cifrado con contraseña. No se puede procesar.",
        })
    except pikepdf.PdfError as e:
        result["warnings"].append({
            "type": "CORRUPT",
            "severity": "error",
            "message": f"PDF dañado o inválido: {e}",
        })

    return result


def _find_unembedded_fonts(pdf: pikepdf.Pdf) -> list[str]:
    """Detecta fuentes referenciadas pero no embebidas."""
    unembedded: list[str] = []
    seen: set[str] = set()

    for page in pdf.pages:
        resources = page.obj.get("/Resources")
        if not resources:
            continue
        fonts = resources.get("/Font")
        if not fonts:
            continue
        try:
            for font_name in fonts.keys():
                font = fonts[font_name]
                if isinstance(font, pikepdf.objects.Object):
                    font = pdf.get_object(font.objgen) if font.is_indirect else font
                base_font = str(font.get("/BaseFont", ""))
                if base_font in seen:
                    continue
                seen.add(base_font)
                # Fuentes Type1 estándar no necesitan embedding
                standard_t1 = {
                    "/Courier", "/Courier-Bold", "/Courier-BoldOblique", "/Courier-Oblique",
                    "/Helvetica", "/Helvetica-Bold", "/Helvetica-BoldOblique", "/Helvetica-Oblique",
                    "/Times-Roman", "/Times-Bold", "/Times-BoldItalic", "/Times-Italic",
                    "/Symbol", "/ZapfDingbats",
                }
                if base_font in standard_t1:
                    continue
                # Verificar si tiene descriptor con stream embebido
                descriptor = font.get("/FontDescriptor")
                if descriptor:
                    has_embedding = any(
                        k in descriptor
                        for k in ("/FontFile", "/FontFile2", "/FontFile3")
                    )
                    if not has_embedding:
                        unembedded.append(base_font.lstrip("/"))
                else:
                    if base_font:
                        unembedded.append(base_font.lstrip("/"))
        except Exception:
            continue

    return list(set(unembedded))[:20]  # máximo 20 fuentes reportadas
