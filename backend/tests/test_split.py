"""Tests del servicio pdf_split."""
from pathlib import Path

import pikepdf
import pytest

from app.services.pdf_split import split_pdf, split_by_pages


def _create_pdf(path: Path, num_pages: int = 5) -> Path:
    pdf = pikepdf.Pdf.new()
    for i in range(num_pages):
        page = pikepdf.Dictionary(
            Type=pikepdf.Name.Page,
            MediaBox=pikepdf.Array([0, 0, 595, 842]),
            Contents=pdf.make_stream(f"BT /F1 12 Tf 100 700 Td (Page {i+1}) Tj ET".encode()),
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


class TestSplitPdf:
    def test_split_single_range(self, tmp_path: Path):
        """Extrae páginas 2-4 de un PDF de 5 páginas."""
        src = _create_pdf(tmp_path / "src.pdf", 5)
        outputs = split_pdf(src, [(2, 4)], tmp_path / "out")
        assert len(outputs) == 1
        with pikepdf.open(outputs[0]) as pdf:
            assert len(pdf.pages) == 3

    def test_split_multiple_ranges(self, tmp_path: Path):
        """Extrae dos rangos → dos archivos."""
        src = _create_pdf(tmp_path / "src.pdf", 6)
        outputs = split_pdf(src, [(1, 2), (4, 6)], tmp_path / "out")
        assert len(outputs) == 2
        with pikepdf.open(outputs[0]) as pdf:
            assert len(pdf.pages) == 2
        with pikepdf.open(outputs[1]) as pdf:
            assert len(pdf.pages) == 3

    def test_split_by_pages(self, tmp_path: Path):
        """Split página a página: N páginas → N archivos de 1 página."""
        src = _create_pdf(tmp_path / "src.pdf", 4)
        outputs = split_by_pages(src, tmp_path / "out")
        assert len(outputs) == 4
        for o in outputs:
            with pikepdf.open(o) as pdf:
                assert len(pdf.pages) == 1

    def test_split_preserves_original(self, tmp_path: Path):
        """El original no debe modificarse."""
        import hashlib
        src = _create_pdf(tmp_path / "src.pdf", 3)
        hash_before = hashlib.sha256(src.read_bytes()).hexdigest()
        split_pdf(src, [(1, 2)], tmp_path / "out")
        assert hashlib.sha256(src.read_bytes()).hexdigest() == hash_before

    def test_split_invalid_range_raises(self, tmp_path: Path):
        """Rango fuera de límites debe lanzar ValueError."""
        src = _create_pdf(tmp_path / "src.pdf", 3)
        with pytest.raises(ValueError, match="fuera de rango"):
            split_pdf(src, [(1, 10)], tmp_path / "out")

    def test_split_zero_start_raises(self, tmp_path: Path):
        """Rango que empieza en 0 es inválido (1-indexed)."""
        src = _create_pdf(tmp_path / "src.pdf", 3)
        with pytest.raises(ValueError):
            split_pdf(src, [(0, 2)], tmp_path / "out")
