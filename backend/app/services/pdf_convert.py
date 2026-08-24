"""Servicio de conversión Office → PDF vía LibreOffice headless."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _find_soffice() -> str | None:
    """Localiza el ejecutable de LibreOffice en PATH o rutas típicas."""
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found

    candidates = [
        os.environ.get("LIBREOFFICE_PATH", ""),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        Path.home() / "LibreOfficeExtract" / "program" / "soffice.exe",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return str(c)
    return None


def convert_to_pdf(input_path: Path, output_dir: Path, timeout: int = 120) -> Path:
    """
    Convierte un documento Office a PDF usando LibreOffice headless.

    LibreOffice se ejecuta en un directorio temporal aislado para evitar
    conflictos cuando múltiples conversiones corren en paralelo.

    Args:
        input_path: Ruta del documento de entrada (.docx, .xlsx, .pptx, etc.)
        output_dir: Directorio donde se guardará el PDF resultante.
        timeout: Tiempo máximo de espera en segundos (default: 120).

    Returns:
        Ruta del PDF generado.

    Raises:
        FileNotFoundError: Si LibreOffice no está instalado o el input no existe.
        RuntimeError: Si la conversión falla.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {input_path}")

    soffice = _find_soffice()
    if soffice is None:
        raise FileNotFoundError(
            "LibreOffice no está instalado o no está en PATH. "
            "Define LIBREOFFICE_PATH apuntando a soffice.exe."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Directorio de perfil temporal para aislamiento de instancias paralelas
    with tempfile.TemporaryDirectory(prefix="lo_profile_") as profile_dir:
        cmd = [
            soffice,
            "--headless",
            "--norestore",
            "--nofirststartwizard",
            f"-env:UserInstallation={Path(profile_dir).as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(input_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice falló (código {result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    # LibreOffice nombra el output con el mismo stem + .pdf
    expected_output = output_dir / (input_path.stem + ".pdf")
    if not expected_output.exists():
        raise FileNotFoundError(
            f"LibreOffice no produjo el PDF esperado en: {expected_output}\n"
            f"STDOUT: {result.stdout}"
        )

    return expected_output
