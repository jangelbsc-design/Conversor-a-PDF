"""Tests del servicio pdf_compress."""
from pathlib import Path

import pikepdf
import pytest

from app.services.pdf_compress import compress_pdf, COMPRESSION_PROFILES


def _create_pdf(path: Path, num_pages: int = 3) -> Path:
    """Crea un PDF con contenido repetido para que la compresión tenga efecto."""
    pdf = pikepdf.Pdf.new()
    # Añadir algo de contenido para que el archivo no sea trivialmente pequeño
    long_text = "Lorem ipsum dolor sit amet. " * 100
    for i in range(num_pages):
        page = pikepdf.Dictionary(
            Type=pikepdf.Name.Page,
            MediaBox=pikepdf.Array([0, 0, 595, 842]),
            Contents=pdf.make_stream(
                f"BT /F1 10 Tf 50 750 Td ({long_text}) Tj ET".encode()
            ),
            Resources=pikepdf.Dictionary(
                Font=pikepdf.Dictionary(
                    F1=pikepdf.Dictionary(
                        Type=pikepdf.Name.Font,
                        Subtype=pikepdf.Name.Type1,
                        BaseFont=pikepdf.Name.Helvetica,
                    )
                )
            ),
        )
        pdf.pages.append(pikepdf.Page(page))
    pdf.save(path)
    return path


class TestCompressPdf:
    def test_compress_level_1(self, tmp_path: Path):
        """Compresión nivel 1 genera un PDF válido."""
        src = _create_pdf(tmp_path / "src.pdf")
        out = tmp_path / "compressed.pdf"
        metrics = compress_pdf(src, out, level=1)
        assert out.exists()
        assert metrics["size_before_bytes"] > 0
        assert metrics["size_after_bytes"] > 0
        # El output debe ser un PDF válido
        with pikepdf.open(out) as pdf:
            assert len(pdf.pages) == 3

    def test_compress_level_2(self, tmp_path: Path):
        """Nivel 2 produce métricas correctas."""
        src = _create_pdf(tmp_path / "src.pdf")
        out = tmp_path / "compressed.pdf"
        metrics = compress_pdf(src, out, level=2)
        assert isinstance(metrics["reduction_percent"], float)

    def test_compress_level_3(self, tmp_path: Path):
        """Nivel 3 también funciona."""
        src = _create_pdf(tmp_path / "src.pdf")
        out = tmp_path / "compressed.pdf"
        metrics = compress_pdf(src, out, level=3)
        assert out.exists()

    def test_compress_preserves_original(self, tmp_path: Path):
        """Original no modificado."""
        import hashlib
        src = _create_pdf(tmp_path / "src.pdf")
        hash_before = hashlib.sha256(src.read_bytes()).hexdigest()
        compress_pdf(src, tmp_path / "out.pdf", level=2)
        assert hashlib.sha256(src.read_bytes()).hexdigest() == hash_before

    def test_compress_invalid_level(self, tmp_path: Path):
        """Nivel inválido lanza ValueError."""
        src = _create_pdf(tmp_path / "src.pdf")
        with pytest.raises(ValueError, match="inválido"):
            compress_pdf(src, tmp_path / "out.pdf", level=99)

    def test_compress_missing_file(self, tmp_path: Path):
        """Archivo inexistente lanza FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compress_pdf(tmp_path / "no_existe.pdf", tmp_path / "out.pdf")

    def test_all_profiles_have_description(self):
        """Todos los perfiles tienen descripción."""
        for level, profile in COMPRESSION_PROFILES.items():
            assert "description" in profile, f"Nivel {level} sin descripción"
