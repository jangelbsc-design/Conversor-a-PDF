# ============================================================
#  PDF Suite Local - PREPARAR (primera vez)
#  Instala todo lo necesario SIN permisos de administrador:
#   1. Python 3.13 (si falta, descarga instalador por-usuario)
#   2. Entorno virtual + dependencias pip
#   3. Node.js portable ZIP (si falta) + npm install
#   4. Genera backend\.env con rutas y clave secreta unicas
#   5. (Opcional) LibreOffice portable para Office -> PDF
# ============================================================
#requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root     = $PSScriptRoot
$ToolsDir = Join-Path $Root "tools"
$LogsDir  = Join-Path $Root "logs"
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
New-Item -ItemType Directory -Force -Path $ToolsDir, $LogsDir | Out-Null

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    [!!] $msg" -ForegroundColor Yellow }

Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  PDF Suite Local - PREPARACION INICIAL"      -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

# ------------------------------------------------------------
# 1. PYTHON
# ------------------------------------------------------------
Step "Verificando Python..."
$Python = $null
foreach ($cand in @("python", "py")) {
    try {
        $v = & $cand --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -match "Python 3\.(\d+)") {
            if ([int]$Matches[1] -ge 11) { $Python = $cand; break }
        }
    } catch {}
}

if (-not $Python) {
    Warn "No hay Python 3.11+ en PATH."
    $ans = Read-Host "Descargar Python 3.13 e instalarlo SOLO para tu usuario? (S/n)"
    if ($ans -notmatch "^[nN]") {
        $PyInstaller = Join-Path $ToolsDir "python-3.13.1-amd64.exe"
        $Url = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-amd64.exe"
        Write-Host "    Descargando desde python.org (~25 MB)..."
        curl.exe -L --fail -o "$PyInstaller" $Url
        if ($LASTEXITCODE -ne 0) { throw "Fallo la descarga de Python. Instalalo manual: https://www.python.org/downloads/ (marca 'Add to PATH')" }
        Write-Host "    Abriendo instalador... marca 'Add python.exe to PATH' y pulsa Install."
        Start-Process -FilePath $PyInstaller -ArgumentList "InstallAllUsers=0","PrependPath=1","Include_test=0" -Wait
        # Refrescar PATH de esta sesion
        $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
        foreach ($cand in @("python", "py")) {
            try { $v = & $cand --version 2>$null; if ($LASTEXITCODE -eq 0) { $Python = $cand; break } } catch {}
        }
        if (-not $Python) { throw "Python sigue sin detectarse. Cierra esta ventana, abre una nueva y vuelve a ejecutar PREPARAR.bat" }
    } else {
        throw "Se necesita Python 3.11+. Descargalo de https://www.python.org/downloads/ (instalacion por usuario, 'Add to PATH') y vuelve a ejecutar este script."
    }
}
Ok "Python detectado: $(& $Python --version)"

# ------------------------------------------------------------
# 2. ENTORNO VIRTUAL + PIP
# ------------------------------------------------------------
$VenvDir = Join-Path $Backend ".venv"
$VenvPy  = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Step "Creando entorno virtual Python..."
    & $Python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual." }
}
Ok "Entorno virtual: backend\.venv"

Step "Instalando dependencias de Python (puede tardar varios minutos)..."
& $VenvPy -m pip install --disable-pip-version-check --no-input -r (Join-Path $Backend "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Warn "pip fallo. Si tu red usa proxy, configura primero:"
    Write-Host '         & .\backend\.venv\Scripts\python.exe -m pip config set global.proxy http://proxy:puerto' -ForegroundColor Gray
    throw "Instalacion de dependencias Python incompleta."
}
Ok "Dependencias Python instaladas."

# ------------------------------------------------------------
# 3. NODE.JS
# ------------------------------------------------------------
Step "Verificando Node.js..."
$NodeVersion = "v22.14.0"
$NodeZipName = "node-$NodeVersion-win-x64"
$LocalNodeDir = Join-Path $ToolsDir $NodeZipName
$LocalNpm = Join-Path $LocalNodeDir "npm.cmd"

$NpmCmd = $null
try {
    $c = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($c) { $NpmCmd = $c.Source }
} catch {}
if (-not $NpmCmd -and (Test-Path $LocalNpm)) {
    $NpmCmd = $LocalNpm
    if (($env:Path -split ";") -notcontains $LocalNodeDir) { $env:Path += ";$LocalNodeDir" }
}

if (-not $NpmCmd) {
    Warn "Node.js no encontrado."
    $ans = Read-Host "Descargar Node.js $NodeVersion portable (~30 MB, sin instalar nada)? (S/n)"
    if ($ans -notmatch "^[nN]") {
        $ZipPath = Join-Path $ToolsDir "$NodeZipName.zip"
        $Url = "https://nodejs.org/dist/$NodeVersion/$NodeZipName.zip"
        Write-Host "    Descargando desde nodejs.org..."
        curl.exe -L --fail -o "$ZipPath" $Url
        if ($LASTEXITCODE -ne 0) { throw "Fallo la descarga de Node. Manual: https://nodejs.org (version ZIP 'Windows Binary')" }
        Write-Host "    Extrayendo..."
        Expand-Archive -Path $ZipPath -DestinationPath $ToolsDir -Force
        Remove-Item $ZipPath -Force
        $NpmCmd = $LocalNpm
        $env:Path += ";$LocalNodeDir"
        # Persistir en el PATH del usuario (no requiere admin)
        $userPath = [Environment]::GetEnvironmentVariable("Path","User")
        if (($userPath -split ";") -notcontains $LocalNodeDir) {
            [Environment]::SetEnvironmentVariable("Path", "$userPath;$LocalNodeDir", "User")
            Ok "Node anadido al PATH del usuario."
        }
    } else {
        throw "Se necesita Node.js 18+. Descargalo de https://nodejs.org y vuelve a ejecutar este script."
    }
}
Ok "npm: $NpmCmd"

Step "Instalando dependencias del frontend (npm install, puede tardar)..."
Push-Location $Frontend
try {
    & $NpmCmd install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) {
        Warn "npm fallo. Si tu red usa proxy:"
        Write-Host "         npm config set proxy http://proxy:puerto" -ForegroundColor Gray
        Write-Host "         npm config set https-proxy http://proxy:puerto" -ForegroundColor Gray
        throw "Instalacion de dependencias frontend incompleta."
    }
} finally { Pop-Location }
Ok "Dependencias frontend instaladas."

# ------------------------------------------------------------
# 4. LIBREOFFICE (opcional, solo para convertir Office -> PDF)
# ------------------------------------------------------------
$Soffice = $null
$LoCandidates = @(
    (Join-Path $env:USERPROFILE "LibreOfficeExtract\program\soffice.exe"),
    (Join-Path $env:LOCALAPPDATA "LibreOfficeExtract\program\soffice.exe"),
    "C:\Program Files\LibreOffice\program\soffice.exe"
)
foreach ($c in $LoCandidates) { if (Test-Path $c) { $Soffice = $c; break } }

if ($Soffice) {
    Ok "LibreOffice ya disponible: $Soffice"
} else {
    Step "LibreOffice NO encontrado (solo afecta a 'Convertir Office a PDF')."
    $ans = Read-Host "Descargar LibreOffice portable y extraerlo sin instalarlo? (~350 MB) (S/n)"
    if ($ans -notmatch "^[nN]") {
        $LoVer = "26.2.5"
        $Msi   = Join-Path $ToolsDir "LibreOffice_${LoVer}_Win_x86-64.msi"
        $LoDir = Join-Path $env:USERPROFILE "LibreOfficeExtract"
        $Ok1 = $false
        foreach ($base in @("https://download.documentfoundation.org", "https://mirror.documentfoundation.org")) {
            $Url = "$base/libreoffice/stable/$LoVer/win/x86_64/LibreOffice_${LoVer}_Win_x86-64.msi"
            Write-Host "    Descargando: $Url"
            curl.exe -L --fail -o "$Msi" $Url
            if ($LASTEXITCODE -eq 0) { $Ok1 = $true; break }
        }
        if (-not $Ok1) {
            Warn "No se pudo descargar LibreOffice (proxy?). La app funcionara sin convertir Office."
            Write-Host "    Manual: baja el MSI de https://es.libreoffice.org y ejecuta:" -ForegroundColor Gray
            Write-Host "    msiexec /a `"$Msi`" TARGETDIR=`"$LoDir`" /qn" -ForegroundColor Gray
        } else {
            Write-Host "    Extrayendo sin instalar (msiexec administrativo, no pide permisos)..."
            Start-Process msiexec.exe -ArgumentList "/a", "`"$Msi`"", "TARGETDIR=`"$LoDir`"", "/qn" -Wait
            Remove-Item $Msi -Force -ErrorAction SilentlyContinue
            if (Test-Path (Join-Path $LoDir "program\soffice.exe")) {
                $Soffice = Join-Path $LoDir "program\soffice.exe"
                Ok "LibreOffice extraido en $LoDir"
            } elseif (Test-Path (Join-Path $LoDir "LibreOffice\program\soffice.exe")) {
                $Soffice = Join-Path $LoDir "LibreOffice\program\soffice.exe"
                Ok "LibreOffice extraido en $LoDir\LibreOffice"
            } else {
                Warn "Extraccion completada pero soffice.exe no aparecio donde se esperaba."
            }
        }
    } else {
        Warn "Sin LibreOffice: todo funciona menos 'Convertir Office a PDF'."
    }
}

# ------------------------------------------------------------
# 5. GENERAR backend\.env
# ------------------------------------------------------------
$EnvFile = Join-Path $Backend ".env"
if (Test-Path $EnvFile) {
    Ok "backend\.env ya existe (no se toca)."
    if ($Soffice) {
        $content = Get-Content $EnvFile -Raw
        if ($content -match "(?m)^LIBREOFFICE_PATH=(.*)$" -and $Matches[1].Trim() -ne $Soffice) {
            $content = $content -replace "(?m)^LIBREOFFICE_PATH=.*$", "LIBREOFFICE_PATH=$Soffice"
            Set-Content -Path $EnvFile -Value $content -Encoding UTF8
            Ok "LIBREOFFICE_PATH actualizado en .env"
        }
    }
} else {
    Step "Generando backend\.env con configuracion local..."
    $bytes = New-Object byte[] 32
    $rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    $rng.GetBytes($bytes)
    $SecretKey = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""

    $StoreDir = Join-Path $Root "store"
    New-Item -ItemType Directory -Force -Path $StoreDir | Out-Null

    $lines = @(
        "# Config LOCAL sin Docker (SQLite en lugar de PostgreSQL)"
        "# Generado automaticamente por PREPARAR.ps1"
        "DATABASE_URL=sqlite+aiosqlite:///$($StoreDir -replace '\\','/')/pdfsuite.db"
        "STORE_PATH=$(($StoreDir) -replace '\\','/')"
        "SECRET_KEY=$SecretKey"
        "MAX_FILE_SIZE_MB=100"
        "DEFAULT_EXPIRY_DAYS=30"
        "CORS_ORIGINS=http://localhost:3000"
    )
    if ($Soffice) { $lines += "LIBREOFFICE_PATH=$Soffice" }
    Set-Content -Path $EnvFile -Value $lines -Encoding ASCII
    Ok "backend\.env creado (clave secreta aleatoria incluida)."
}

# ------------------------------------------------------------
# FIN
# ------------------------------------------------------------
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  PREPARACION COMPLETADA"                      -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Siguiente paso: doble clic en INICIAR.bat" -ForegroundColor White
Write-Host ""
Read-Host "Pulsa ENTER para cerrar esta ventana"
