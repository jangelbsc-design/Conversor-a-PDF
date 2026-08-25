# 📌 RECUÉRDAME — Estado del proyecto "Conversor a PDF"

> Última actualización: 25 de agosto de 2026 (VBS fix)

---

## ⚡ Cómo abrir la app HOY (lo importante primero)

```powershell
# Terminal 1 — Backend (API):
cd "C:\Users\jabustos\Desktop\APP y N8N\Conversor a PDF\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend (web):
cd "C:\Users\jabustos\Desktop\APP y N8N\Conversor a PDF\frontend"
npm run dev
```

| Servicio | URL |
|---|---|
| **App web** | http://localhost:3000 |
| API salud | http://localhost:8000/health |
| Docs Swagger | http://localhost:8000/api/docs |

⚠️ El backend tarda ~7 segundos en estar listo. El proceso de Python se llama `python3.13`
(no `python`) al buscarlo con Get-Process.

---

## 🖥️ Contexto: ¿por qué NO usamos Docker?

- La PC es **corporativa SIN permisos de administrador** (no hay contraseña maestra).
- Docker Desktop está instalado (`C:\Users\jabustos\AppData\Local\Programs\DockerDesktop`)
  pero **no puede arrancar porque falta WSL2**, que requiere admin para instalarse.
- Conclusión: la app corre **nativamente sin Docker**: backend Python directo y SQLite
  en lugar de PostgreSQL. Los cambios son compatibles: si algún día hay admin,
  `docker compose up --build` sigue funcionando igual.

---

## 🔧 Cambios que se hicieron al código (todos compatibles con Postgres/Docker)

1. **Modelos SQLite-compatibles** (backend/app/models/*.py):
   - Reemplazado `sqlalchemy.dialects.postgresql.UUID` por el tipo portable
     `sqlalchemy.Uuid` en los 4 modelos (document, operation, audit, signature).
2. **backend/app/database.py**:
   - `pool_size`/`max_overflow` solo se aplican si la URL es PostgreSQL
     (SQLite no acepta esos parámetros).
3. **backend/app/main.py**:
   - El lifespan crea las tablas automáticamente con `Base.metadata.create_all`
     (en modo local no se usa Alembic).
4. **backend/app/services/pdf_ocr.py**:
   - Import de `ocrmypdf` ahora es perezoso (dentro de función) para que el backend
     arranque aunque OCR no esté disponible.
5. **backend/app/services/pdf_convert.py** (adaptado a Windows):
   - Nueva función `_find_soffice()`: busca soffice.exe en PATH, variable
     `LIBREOFFICE_PATH`, rutas típicas de Windows y `~/LibreOfficeExtract`.
   - URI del perfil corregida: `Path(profile_dir).as_uri()` (antes `file://C:\...` fallaba).
6. **backend/app/utils/file_safety.py**:
   - Agregado `"text/rtf"` a la lista blanca MIME (libmagic en Windows reporta
     así los .rtf; antes los rechazaba).
7. **backend/.env** (NUEVO, no está en git por seguridad):
   - `DATABASE_URL=sqlite+aiosqlite:///C:/.../store/pdfsuite.db` (ruta con espacios
     SIN codificar %20, si no SQLite no abre el archivo).
   - `STORE_PATH=C:/Users/jabustos/Desktop/APP y N8N/Conversor a PDF/store`
   - `SECRET_KEY=<generada aleatoriamente>`
   - `LIBREOFFICE_PATH=C:\Users\jabustos\LibreOfficeExtract\program\soffice.exe`

---

## 📄 Conversor Office → PDF (LibreOffice portable, sin admin)

- Descargado MSI oficial 26.2.5 desde download.documentfoundation.org
  (el proxy corporativo lo permite; portableapps.com está bloqueado).
- **Extraído sin instalarlo** con `msiexec /a` (extracción administrativa, no pide UAC).
- Ubicación: `C:\Users\jabustos\LibreOfficeExtract\program\soffice.exe` (v26.2.5.2).
- Probado end-to-end: DOCX → PDF válido ✓, descargable ✓, audit log ✓.
- Formatos soportados: docx, xlsx, pptx, odt/ods/odp, doc/xls/ppt, rtf, txt.

### Pendientes opcionales (instalables sin admin si algún día hacen falta)
- **Poppler portable** → para miniaturas de vista previa (PagePreview).
- **Tesseract portable** → para OCR.
- Nota: el proxy bloquea portableapps.com pero GitHub funciona (cloudflared,
  poppler-windows de oschwartz10612 se pueden bajar desde GitHub releases).

---

## 🐛 Problemas encontrados y sus soluciones (por si reaparecen)

| Síntoma | Causa | Solución aplicada |
|---|---|---|
| `docker: no se reconoce` | CLI fuera del PATH | Estaba en resources\bin de DockerDesktop |
| `Docker Desktop is unable to start` | Falta WSL2 | No instalable sin admin → plan nativo |
| `unable to open database file` | Espacios codificados %20 en URL SQLite | Ruta sin codificar en DATABASE_URL |
| `Invalid argument(s) 'pool_size'...` | SQLite no acepta parámetros de pool PG | Condional en database.py |
| PowerShell: `No se puede crear un canal seguro SSL/TLS` | TLS viejo / proxy corporativo | Usar curl.exe o python urllib (pypi y github sí funcionan) |
| Backend viejo no moría con Stop-Process python | El proceso se llama `python3.13` | Matar por PID del puerto: `Get-NetTCPConnection -LocalPort 8000` |

---

## ☁️ GitHub

- **Repo**: https://github.com/jangelbsc-design/Conversor-a-PDF (rama `main`)
- Commit inicial `839633c`, 98 archivos.
- **NO subido a propósito** (.gitignore): `.env` (secretos), `store/` (documentos
  personales), `*.db`, `node_modules`, `__pycache__`.
- Para subir cambios futuros:
  ```powershell
  git add -A ; git commit -m "descripción" ; git push
  ```
- Autenticación: Git Credential Manager abrió el navegador la primera vez;
  ya quedó guardada la sesión.

---

## 📱 Acceso desde el teléfono (pendiente, decidido no hacerlo hoy)

GitHub solo guarda el código, no la app corriendo. Opciones cuando se quiera:

1. **Misma red WiFi** (gratis, inmediato): IP local de la PC es `192.168.2.150`.
   Habría que: exponer uvicorn en `0.0.0.0`, agregar CORS de esa IP y arrancar
   Next con `NEXT_PUBLIC_API_URL=http://192.168.2.150:8000`.
2. **Túnel público**: cloudflared (se baja de GitHub, sin admin) → URL accesible
   desde cualquier red; la URL cambia en cada reinicio.

---

## 📦 Distribución por ZIP (creada el 24-ago-2026)

- **ZIP listo para compartir**: `PDF-Suite-Local.zip` (~0,1 MB, solo código).
  Sin secretos (.env), sin store/, sin node_modules/.next/__pycache__.
- Archivos nuevos en la raíz:
  - `PREPARAR.bat/.ps1` → instalación automática sin admin: Python per-user
    (si falta), venv + pip, Node portable ZIP (si falta) + npm install,
    genera `backend\.env` con rutas relativas al script + SECRET_KEY aleatoria,
    LibreOffice opcional descargado y extraído con `msiexec /a` a
    `%USERPROFILE%\LibreOfficeExtract` (misma ruta que ya busca `_find_soffice()`).
  - `INICIAR.bat/.ps1` → arranca backend+frontend, abre navegador.
  - `DETENER.bat/.ps1` → mata procesos por puerto.
  - `LEEME_INSTALAR.md` → guía paso a paso del destinatario.
- Correcciones de portabilidad aplicadas:
  - `requirements.txt`: añadido `aiosqlite==0.22.1` (faltaba, rompía SQLite)
    y `python-magic-bin==0.4.14 ; sys_platform == "win32"` (en Windows el
    paquete correcto es magic-bin, no python-magic).
  - `.gitignore`: añadidos `logs/`, `tools/`, `*.zip`.
- Validado: sintaxis PS OK, URL SQLite con espacios abre OK, ZIP limpio.

---

## 🐛 BUG CRÍTICO + SOLUCIÓN: servicios mueren al cerrar el script

**Problema (resuelto 25-ago-2026)**: `.bat` con `start /min` y PowerShell
`Start-Process` no crean procesos desvinculados. Al cerrar el proceso padre,
los hijos mueren.

**Solución**: VBScript con `WScript.Shell.Run` (WindowStyle=7, bWait=False).
Este método SÍ crea procesos verdaderamente desvinculados del padre en Windows.
Es el approach estándar para servicios background en scripts Windows desde los
años 2000.

- `INICIAR.vbs` → arranca backend+frontend invisibles, abre navegador
- `DETENER.vbs` → mata procesos por puerto + diálogo de confirmación
- Acceso directo "PDF Suite.lnk" en el Escritorio → INICIAR.vbs
- Verificado: procesos vivos después de 75+ segundos, health 200 OK

**Archivos (.bat y .ps1 quedan obsoletos)**:
- `INICIAR.bat` / `INICIAR.ps1` → ya no usar (mueren al salir)
- `DETENER.bat` / `DETENER.ps1` → ya no usar
- **Usar solo**: `INICIAR.vbs` / `DETENER.vbs` o el acceso directo del Escritorio

---

## 🖱️ Uso diario en ESTA máquina (resuelto 25-ago-2026)

- **Un solo ícono en el Escritorio**: "PDF Suite.lnk"
- Doble clic → se abre la app automáticamente en el navegador
- Para cerrar: cerrar la pestaña del navegador (los servicios quedan en
  background y se reutilizan al abrir de nuevo) o ejecutar `DETENER.vbs`
- Los servicios sobreviven al cerrar ventanas, cerrar el script, etc.
- **NO USAR** los `.bat` / `.ps1` (quedan obsoletos, causaban el bug)

---

## ✅ Estado actual de las herramientas de la app

| Herramienta | Estado |
|---|---|
| Unir (merge) | ✅ funcional |
| Dividir (split) | ✅ funcional |
| Comprimir | ✅ funcional |
| **Convertir Office→PDF** | ✅ **funcional (LibreOffice portable)** |
| Marca de agua | ✅ funcional |
| Redactar | ✅ funcional |
| Rotar / Reordenar | ✅ funcional |
| Firma local | ✅ funcional |
| Vista previa de páginas | ⚠️ requiere Poppler (pendiente) |
| OCR | ❌ requiere Tesseract (pendiente) |
