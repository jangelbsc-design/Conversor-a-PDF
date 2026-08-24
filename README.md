# PDF Suite Local — Reemplazo Personal de ILovePDF Premium

> ⚠️ **AVISO OBLIGATORIO DE BAJO RIESGO**: Esta herramienta está diseñada para uso personal, privado y de bajo riesgo. **NO produce firmas electrónicas cualificadas o avanzadas (eIDAS / ESIGN Act)**, no realiza verificación de identidad gubernamental ni reemplaza la edición vectorial especializada ni la gobernanza documental corporativa.

---

## 🌟 Características Principales

- **100% On-Premise y Privado**: No existen llamadas a servidores de terceros, ni telemetría, ni analytics, ni cuentas en la nube.
- **Inmutabilidad y Versionado**: Los archivos originales subidos se guardan como solo lectura y **nunca se sobrescriben**. Cada transformación produce un archivo versionado único con identificador UUID y marca de tiempo.
- **Log de Auditoría Append-Only**: Registro secuencial inmutable con marcas de tiempo UTC, hashes SHA-256 antes y después de cada operación.
- **Inspección Previa Inteligente**: Detección y advertencia de formularios AcroForm, firmas digitales existentes, cifrado y fuentes no embebidas.
- **Exportación Directa**: Respaldo completo en un solo clic descargable como `.zip` con todos los originales, outputs y el log de auditoría `audit.jsonl`.

### 🛠️ Herramientas Soportadas

1. **Unir (Merge)**: Combina $N$ PDFs manteniendo los originales intactos.
2. **Dividir (Split)**: Extracción por rangos de páginas o partición página por página en `.zip`.
3. **Comprimir (Compress)**: Tres niveles de compresión (ligera, media y agresiva) con métricas de reducción en tiempo real.
4. **Convertir Office a PDF**: Conversión de `.docx`, `.xlsx`, `.pptx`, `.odt` vía LibreOffice headless en perfiles aislados.
5. **Marca de Agua (Watermark)**: Sellos de texto con opacidad, rotación y tamaño configurables.
6. **Redactar / Ocultar (Redact)**: Aplicación de recuadros negros opacos por coordenadas de página.
7. **Reconocimiento Óptico (OCR)**: Inserción de capa de texto buscable con Tesseract (Español + Inglés) y corrección de inclinación (*deskew*).
8. **Rotar Páginas (Rotate)**: Giro de 90°, 180° o 270° sobre el árbol del PDF sin recodificar imágenes.
9. **Reordenar (Reorder)**: Reorganización o duplicación de páginas mediante secuencias arbitrarias.
10. **Firma y Sellado Local (Sign)**: Colocación de campos, aceptación explícita de términos y sellado con hash SHA-256.

---

## 🏗️ Arquitectura Técnica

```
├── docker-compose.yml           # Orquestación con un solo comando
├── .env.example                 # Plantilla de variables de entorno
│
├── backend/                     # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── services/            # Motor PDF (pikepdf, LibreOffice, OCRmyPDF, Pillow)
│   │   ├── routers/             # Endpoints REST (merge, split, compress, sign, etc.)
│   │   ├── models/              # Modelos SQLAlchemy (PostgreSQL)
│   │   ├── schemas/             # Pydantic v2
│   │   └── utils/               # Hash SHA-256, saneamiento de nombres, audit append-only
│   ├── alembic/                 # Migraciones de base de datos
│   └── tests/                   # Suite de pruebas unitarias y e2e (pytest + anyio)
│
├── frontend/                    # Next.js 15 (App Router + TypeScript)
│   ├── app/                     # Páginas y layout de la suite
│   ├── components/              # Componentes UI (UploadZone, PagePreview, AuditLog, etc.)
│   └── lib/api.ts               # Cliente API tipado
│
└── store/                       # Almacenamiento local persistente
    ├── originals/               # Archivos originales inmutables
    ├── outputs/                 # Salidas versionadas por operación
    ├── previews/                # Miniaturas PNG en caché
    └── audit.jsonl              # Log de auditoría append-only
```

---

## 🚀 Puesta en Marcha (Primer Uso con 1 Comando)

### Prerrequisitos
- [Docker](https://www.docker.com/) y Docker Compose instalados.

### 1. Configurar variables de entorno
Copia la plantilla de configuración:
```bash
cp .env.example .env
```

*(Opcional: edita `.env` para personalizar contraseñas locales).*

### 2. Iniciar el stack completo
Ejecuta el siguiente comando:
```bash
docker compose up --build
```

Una vez levantado:
- **Frontend Web**: [http://localhost:3000](http://localhost:3000)
- **API Backend**: [http://localhost:8000](http://localhost:8000)
- **Documentación Swagger / OpenAPI**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

---

## 💾 Ubicación de Datos y Copias de Seguridad (Backup)

Todos los datos se guardan dentro de tu propia máquina en el directorio `./store`:

- `./store/originals/<uuid>/<nombre>`: Archivos tal cual fueron cargados.
- `./store/outputs/<op_id>/<nombre>`: Archivos transformados.
- `./store/audit.jsonl`: Registro cronológico en formato JSON Lines.

### Descarga de Backup
Puedes descargar una copia de seguridad íntegra directamente desde la interfaz web o mediante el endpoint:
```bash
curl -O http://localhost:8000/api/backup/download
```

---

## 🧪 Ejecución de Pruebas Automatizadas

Para validar las transformaciones del motor PDF y el happy path de extremo a extremo:

### Ejecutar tests dentro de Docker:
```bash
docker compose exec backend pytest -v
```

### O localmente en entorno Python:
```bash
cd backend
pytest -v
```

### Pruebas cubiertas:
- ✅ `tests/test_merge.py`: Preservación de originales, conteo de páginas y validación de entradas.
- ✅ `tests/test_split.py`: Extracción por rangos y split página a página.
- ✅ `tests/test_compress.py`: Los 3 niveles de compresión y reporte de reducción.
- ✅ `tests/test_e2e_happy_path.py`: Flujo completo de subida, validación MIME, combinación y soft-delete.

---

## 🛡️ Límites y Exclusiones Deliberadas

Con el fin de garantizar simplicidad y seguridad en un entorno personal y autónomo:
- ❌ **Sin cuentas ni gestión de usuarios multi-tenant.**
- ❌ **Sin pasarelas de pago ni planes premium.**
- ❌ **Sin telemetría ni comunicación con servicios externos.**
- ❌ **Sin emisión de certificados cualificados ni validación con eIDAS/ESIGN.**
