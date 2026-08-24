FROM python:3.12-slim

# ── Variables de build ─────────────────────────────────────────────
ARG DEBIAN_FRONTEND=noninteractive

# ── Dependencias del sistema ───────────────────────────────────────
# LibreOffice headless, Tesseract OCR, poppler, qpdf, ghostscript
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    qpdf \
    ghostscript \
    libmagic1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Directorio de trabajo ──────────────────────────────────────────
WORKDIR /app

# ── Instalar dependencias Python ───────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copiar código fuente ───────────────────────────────────────────
COPY . .

# ── Crear directorios del store ────────────────────────────────────
RUN mkdir -p /store/originals /store/outputs /store/previews

# ── Healthcheck ────────────────────────────────────────────────────
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
