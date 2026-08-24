"""Tests del servicio pdf_merge."""
import tempfile
from pathlib import Path

import pikepdf
import pytest

from app.services.pdf_merge import merge_pdfs


def _create_pdf(path: Path, num_pages: int = 1, title: str = "Test") -> Path:
    """Helper: crea un PDF mínimo con N páginas."""
    pdf = pikepdf.Pdf.new()
    for i in range(num_pages):
        page = pikepdf.Dictionary(
            Type=pikepdf.Name.Page,
            MediaBox=pikepdf.Array([0, 0, 595, 842]),
            Contents=pdf.make_stream(f"BT /F1 12 Tf 100 700 Td ({title} p{i+1}) Tj ET".encode()),
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


class TestMergePdfs:
    def test_merge_two_pdfs(self, tmp_path: Path):
        """Combina dos PDFs de 2 páginas → resultado de 4 páginas."""
        a = _create_pdf(tmp_path / "a.pdf", num_pages=2, title="A")
        b = _create_pdf(tmp_path / "b.pdf", num_pages=2, title="B")
        out = tmp_path / "merged.pdf"

        merge_pdfs([a, b], out)

        assert out.exists()
        with pikepdf.open(out) as pdf:
            assert len(pdf.pages) == 4

    def test_merge_preserves_originals(self, tmp_path: Path):
        """Los archivos originales no deben modificarse."""
        a = _create_pdf(tmp_path / "a.pdf", num_pages=1)
        b = _create_pdf(tmp_path / "b.pdf", num_pages=1)

        import hashlib
        def file_hash(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()

        hash_a_before = file_hash(a)
        hash_b_before = file_hash(b)

        out = tmp_path / "merged.pdf"
        merge_pdfs([a, b], out)

        assert file_hash(a) == hash_a_before, "El original A fue modificado"
        assert file_hash(b) == hash_b_before, "El original B fue modificado"

    def test_merge_three_pdfs(self, tmp_path: Path):
        """Combina tres PDFs."""
        pdfs = []
        for i, pages in enumerate([1, 3, 2]):
            p = _create_pdf(tmp_path / f"{i}.pdf", num_pages=pages)
            pdfs.append(p)
        out = tmp_path / "merged3.pdf"
        merge_pdfs(pdfs, out)
        with pikepdf.open(out) as pdf:
            assert len(pdf.pages) == 6

    def test_merge_empty_list_raises(self, tmp_path: Path):
        """Lista vacía debe lanzar ValueError."""
        with pytest.raises(ValueError, match="al menos"):
            merge_pdfs([], tmp_path / "out.pdf")

    def test_merge_missing_file_raises(self, tmp_path: Path):
        """Archivo inexistente debe lanzar FileNotFoundError."""
        a = _create_pdf(tmp_path / "a.pdf", num_pages=1)
        missing = tmp_path / "no_existe.pdf"
        with pytest.raises(FileNotFoundError):
            merge_pdfs([a, missing], tmp_path / "out.pdf")

    def test_output_is_valid_pdf(self, tmp_path: Path):
        """El output debe ser un PDF válido que pikepdf pueda abrir."""
        a = _create_pdf(tmp_path / "a.pdf", num_pages=2)
        out = tmp_path / "merged.pdf"
        merge_pdfs([a], out)
        # No debe lanzar excepción
        with pikepdf.open(out) as pdf:
            assert len(pdf.pages) >= 1
