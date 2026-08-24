"""
Test e2e happy path: sube un PDF y lo combina con otro (merge).

Este test usa httpx.AsyncClient contra la app FastAPI en modo de prueba.
Usa SQLite en lugar de PostgreSQL para no requerir Docker en CI.
"""
import io
import os
import tempfile
from pathlib import Path

import pikepdf
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Configurar base de datos de prueba ANTES de importar la app
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("STORE_PATH", tempfile.mkdtemp(prefix="pdf_suite_test_"))

from app.database import Base, get_db
from app.main import app


def _make_pdf_bytes(num_pages: int = 2) -> bytes:
    """Crea un PDF mínimo en memoria."""
    buf = io.BytesIO()
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
    pdf.save(buf)
    return buf.getvalue()


@pytest_asyncio.fixture
async def db_engine():
    """Motor SQLite en memoria para pruebas."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine):
    """Cliente HTTP async con DB de prueba."""
    TestSessionLocal = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """El endpoint /health debe responder 200."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_and_list(client: AsyncClient):
    """Sube un PDF y lo encuentra en la lista de documentos."""
    pdf_bytes = _make_pdf_bytes(2)
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["filename_safe"] == "test.pdf"
    assert data["sha256"] != ""
    doc_id = data["id"]

    # Verificar en la lista
    list_resp = await client.get("/api/documents/")
    assert list_resp.status_code == 200
    ids = [d["id"] for d in list_resp.json()["documents"]]
    assert doc_id in ids


@pytest.mark.asyncio
async def test_upload_invalid_mime_rejected(client: AsyncClient):
    """Archivos no-PDF/Office deben ser rechazados."""
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("malware.exe", b"\x4d\x5a\x90\x00", "application/octet-stream")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_merge_happy_path(client: AsyncClient):
    """
    Happy path completo:
    1. Sube dos PDFs
    2. Los combina
    3. Verifica que el output tiene el número correcto de páginas
    """
    pdf_a = _make_pdf_bytes(2)
    pdf_b = _make_pdf_bytes(3)

    # Upload A
    resp_a = await client.post(
        "/api/documents/upload",
        files={"file": ("doc_a.pdf", pdf_a, "application/pdf")},
    )
    assert resp_a.status_code == 201
    id_a = resp_a.json()["id"]

    # Upload B
    resp_b = await client.post(
        "/api/documents/upload",
        files={"file": ("doc_b.pdf", pdf_b, "application/pdf")},
    )
    assert resp_b.status_code == 201
    id_b = resp_b.json()["id"]

    # Merge
    merge_resp = await client.post(
        "/api/merge/",
        json={"doc_ids": [id_a, id_b]},
    )
    assert merge_resp.status_code == 200, merge_resp.text
    merge_data = merge_resp.json()
    assert merge_data["status"] == "success"
    assert merge_data["output_sha256"] is not None

    # Verificar el PDF resultante
    out_path = Path(merge_data["output_path"])
    assert out_path.exists()
    with pikepdf.open(out_path) as pdf:
        assert len(pdf.pages) == 5  # 2 + 3

    # Verificar que los originales siguen intactos
    doc_a = await client.get(f"/api/documents/{id_a}")
    assert doc_a.json()["sha256"] == resp_a.json()["sha256"]
    doc_b = await client.get(f"/api/documents/{id_b}")
    assert doc_b.json()["sha256"] == resp_b.json()["sha256"]


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient):
    """Soft-delete: el documento desaparece de la lista pero no del disco."""
    pdf_bytes = _make_pdf_bytes(1)
    upload = await client.post(
        "/api/documents/upload",
        files={"file": ("to_delete.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload.json()["id"]
    original_path = Path(upload.json().get("original_path", ""))

    # Eliminar
    del_resp = await client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 204

    # Ya no aparece en la lista
    list_resp = await client.get("/api/documents/")
    ids = [d["id"] for d in list_resp.json()["documents"]]
    assert doc_id not in ids
