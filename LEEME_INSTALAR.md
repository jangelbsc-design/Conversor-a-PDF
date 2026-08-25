# 📦 PDF Suite Local — Guía de instalación (PC corporativa, sin administrador)

Suite de herramientas PDF **100% local**: nada se sube a internet, todo queda en tu máquina.
Incluye: unir, dividir, comprimir, marca de agua, redactar, rotar/reordenar, firma local,
auditoría y conversión Office→PDF.

---

## ⚡ Instalación en 3 pasos

### Paso 0 — Descomprimir
Descomprime el ZIP en una carpeta de tu usuario, por ejemplo:

```
C:\Users\tu.usuario\PDF Suite
```

> Si Windows marcó los archivos como "bloqueados" (SmartScreen):
> clic derecho sobre cada `.bat` → Propiedades → **Desbloquear** → Aceptar.

### Paso 1 — PREPARAR.bat  *(solo la primera vez)*

Doble clic en `PREPARAR.bat`. El script hace todo solo, **sin pedir permisos de administrador**:

| ¿Qué instala? | Cómo | Tamaño |
|---|---|---|
| Python 3.13 | Instalador oficial *solo para tu usuario* (si ya lo tienes, lo salta) | ~25 MB |
| Librerías del backend | `pip install` en un entorno virtual dentro de la carpeta | ~150 MB |
| Node.js | Versión portable ZIP, sin instalador (si ya lo tienes, lo salta) | ~30 MB |
| Dependencias frontend | `npm install` | ~400 MB |
| LibreOffice *(opcional)* | MSI oficial extraído con `msiexec /a`, sin instalación real | ~350 MB |

LibreOffice **solo** es necesario para la herramienta *Convertir Office→PDF*
(Word/Excel/PowerPoint → PDF). Si lo omites o falla la descarga, el resto funciona igual.

### Paso 2 — INICIAR.bat

Doble clic en `INICIAR.bat` (cada vez que quieras usar la app):

1. Arranca el backend y el frontend.
2. Espera a que ambos respondan.
3. Abre tu navegador en **http://localhost:3000**

Para cerrar la app: doble clic en **DETENER.bat**.

---

## 📁 Qué se crea en la carpeta

```
store\          ← tus documentos procesados (NO borrar si quieres conservarlos)
logs\           ← registros de arranque (útil si algo falla)
tools\          ← Node/LibreOffice descargados (se puede borrar tras instalar)
backend\.venv\  ← entorno Python aislado
backend\.env    ← configuración generada automáticamente (no compartir)
```

---

## 🔧 Problemas frecuentes

| Síntoma | Solución |
|---|---|
| Windows protegió el archivo .bat | Clic derecho → Propiedades → Desbloquear |
| "No se puede ejecutar scripts" | Usar los `.bat`, no los `.ps1` directamente |
| `pip` falla con error SSL/red | Tu red usa proxy: `backend\.venv\Scripts\python.exe -m pip config set global.proxy http://proxy:puerto` y repetir PREPARAR |
| `npm install` falla | `npm config set proxy http://proxy:puerto` y `npm config set https-proxy http://proxy:puerto`, luego repetir PREPARAR |
| La web tarda en abrir | Normal la primera vez (compilación inicial de Next.js); las siguientes veces es rápido |
| Puerto 8000/3000 ocupado | INICIAR ofrece terminar el proceso anterior automáticamente |
| No aparece "Convertir Office→PDF" disponible | Falta LibreOffice: vuelve a lanzar PREPARAR.bat y acepta su descarga |

---

## 🔒 Privacidad

- Todo corre en **localhost**: ni un byte sale de tu equipo.
- Los documentos se guardan en `store\` y puedes borrarlos cuando quieras.
- Sin cuentas, sin telemetría, sin servicios cloud.

---

## ✅ Disponibilidad de herramientas

| Herramienta | Requisito |
|---|---|
| Unir / Dividir / Comprimir / Marca de agua / Redactar / Rotar / Reordenar / Firma | Incluido ✓ |
| Convertir Office→PDF (docx, xlsx, pptx, odt…) | LibreOffice (opcional, PREPARAR lo instala) |
| Vista previa de páginas | Requiere Poppler (no incluido) |
| OCR | Requiere Tesseract (no incluido) |
