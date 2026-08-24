"""
Servicio de firma: coloca campos, registra consentimiento y sella hash final.

⚠️ AVISO LEGAL IMPORTANTE:
Este módulo NO produce firmas electrónicas cualificadas ni avanzadas
según eIDAS, ESIGN Act, ni ningún otro marco regulatorio.
- No usa certificados de CA cualificada.
- No verifica identidad del firmante.
- No garantiza no-repudio legal.
- Está diseñado EXCLUSIVAMENTE para uso personal de bajo riesgo.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pikepdf
from pikepdf import Array, Dictionary, Name


def place_signature_fields(
    input_path: Path,
    output_path: Path,
    fields: list[dict[str, Any]],
) -> None:
    """
    Añade campos de firma visuales (anotaciones) a las páginas.

    Los campos son anotaciones Widget visibles pero NO firmas criptográficas.

    Args:
        fields: Lista de {page, x, y, width, height, label, field_type}
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
        for field in fields:
            page_num = int(field["page"]) - 1
            if page_num < 0 or page_num >= len(pdf.pages):
                raise ValueError(f"Página {field['page']} fuera de rango.")

            page = pdf.pages[page_num]
            x, y, w, h = float(field["x"]), float(field["y"]), float(field["width"]), float(field["height"])
            label = str(field.get("label", "Firma"))

            # Anotación visual (cuadro de firma con borde azul)
            annotation = pdf.make_indirect(Dictionary(
                Type=Name("/Annot"),
                Subtype=Name("/Square"),
                Rect=Array([x, y, x + w, y + h]),
                C=Array([0.0, 0.4, 0.8]),   # borde azul
                IC=Array([0.9, 0.95, 1.0]),  # relleno azul muy claro
                BS=Dictionary(W=2, S=Name("/S")),
                Contents=pikepdf.String(f"[{label}]"),
                T=pikepdf.String(label),
                F=4,  # Print flag
            ))

            annots = page.obj.get("/Annots", pikepdf.Array())
            annots.append(annotation)
            page.obj["/Annots"] = annots

        pdf.save(output_path, compress_streams=True)


def record_consent_and_seal(
    signed_path: Path,
    output_path: Path,
    signer_name: str,
    consent_text: str,
    ip_address: str = "127.0.0.1",
) -> dict[str, str]:
    """
    Registra consentimiento y sella el PDF con metadata + hash SHA-256.

    El sellado añade metadata de consentimiento al PDF y calcula
    el hash del archivo final (para el audit log).

    Returns:
        Dict con final_hash y timestamp de sellado.
    """
    if not signed_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {signed_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()

    consent_record = {
        "signer_name": signer_name,
        "consent_text": consent_text,
        "consent_timestamp_utc": timestamp,
        "consent_ip_local": ip_address,
        "disclaimer": (
            "ESTO NO ES UNA FIRMA ELECTRÓNICA CUALIFICADA. "
            "Es un registro de consentimiento personal de bajo riesgo. "
            "No tiene validez legal equivalente a una firma certificada."
        ),
    }

    with pikepdf.open(signed_path, allow_overwriting_input=False) as pdf:
        with pdf.open_metadata() as meta:
            meta["pdf:ConsentRecord"] = json.dumps(consent_record, ensure_ascii=False)
            meta["pdf:SignedBy"] = signer_name
            meta["pdf:SignedAt"] = timestamp
            meta["xmp:ModifyDate"] = timestamp

        pdf.save(output_path, compress_streams=True)

    # Calcular hash del PDF sellado
    h = hashlib.sha256()
    with open(output_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    final_hash = h.hexdigest()

    return {
        "final_hash": final_hash,
        "sealed_at": timestamp,
        "signer_name": signer_name,
    }
