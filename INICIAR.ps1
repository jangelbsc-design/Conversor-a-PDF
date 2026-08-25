# ============================================================
#  PDF Suite Local - INICIAR
#  Arranca backend (puerto 8000) y frontend (puerto 3000),
#  espera a que ambos respondan y abre el navegador.
# ============================================================
#requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root     = $PSScriptRoot
$LogsDir  = Join-Path $Root "logs"
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    [!!] $msg" -ForegroundColor Yellow }

Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  PDF Suite Local - INICIO"                    -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

# ------------------------------------------------------------
# Comprobaciones previas
# ------------------------------------------------------------
if (-not (Test-Path (Join-Path $Backend ".env"))) {
    throw "Falta backend\.env. Ejecuta primero PREPARAR.bat"
}
$VenvPy = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    throw "Falta el entorno virtual Python. Ejecuta primero PREPARAR.bat"
}

function Test-FreePort($port, $name) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $pids = ($conn.OwningProcess | Sort-Object -Unique) -join ", "
        Warn "El puerto $port ($name) ya esta ocupado por el proceso PID $pids."
        $ans = Read-Host "    Terminar ese proceso y continuar? (S/n)"
        if ($ans -notmatch "^[nN]") {
            foreach ($procId in ($conn.OwningProcess | Sort-Object -Unique)) {
                try { taskkill /PID $procId /T /F 2>$null | Out-Null } catch {}
            }
            Start-Sleep -Seconds 1
        } else {
            throw "Puerto $port ocupado; libera el puerto y vuelve a intentarlo."
        }
    }
}
Test-FreePort 8000 "API backend"
Test-FreePort 3000 "web frontend"

# Node local (si se instalo con PREPARAR)
$LocalNodeDir = Get-ChildItem -Directory (Join-Path $Root "tools") -Filter "node-*" -ErrorAction SilentlyContinue |
                Select-Object -First 1
if ($LocalNodeDir) { $env:Path += ";" + $LocalNodeDir.FullName }

# ------------------------------------------------------------
# Backend
# ------------------------------------------------------------
Step "Arrancando API backend (puerto 8000)..."
$BkProc = Start-Process -FilePath $VenvPy `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -WorkingDirectory $Backend -WindowStyle Minimized -PassThru `
    -RedirectStandardOutput (Join-Path $LogsDir "backend.log") `
    -RedirectStandardError  (Join-Path $LogsDir "backend.err.log")
$BkProc.Id | Set-Content (Join-Path $LogsDir "backend.pid")

$Ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $Ready = $true; break }
    } catch {}
}
if (-not $Ready) {
    Warn "El backend no respondio en 30 s. Revisa logs\backend.err.log"
} else {
    Ok "API lista en http://localhost:8000"
}

# ------------------------------------------------------------
# Frontend
# ------------------------------------------------------------
Step "Arrancando web frontend (puerto 3000)..."
$NpmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $NpmCmd -and $LocalNodeDir) { $NpmCmd = Join-Path $LocalNodeDir.FullName "npm.cmd" }
if (-not $NpmCmd) { throw "npm no encontrado. Ejecuta PREPARAR.bat" }

$FeProc = Start-Process -FilePath $NpmCmd `
    -ArgumentList "run","dev" `
    -WorkingDirectory $Frontend -WindowStyle Minimized -PassThru `
    -RedirectStandardOutput (Join-Path $LogsDir "frontend.log") `
    -RedirectStandardError  (Join-Path $LogsDir "frontend.err.log")
$FeProc.Id | Set-Content (Join-Path $LogsDir "frontend.pid")

$Ready = $false
for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $Ready = $true; break }
    } catch {}
}
if (-not $Ready) {
    Warn "La web no respondio en 90 s (la primera vez Next tarda mas). Revisa logs\frontend.err.log"
} else {
    Ok "Web lista en http://localhost:3000"
}

# ------------------------------------------------------------
# Navegador
# ------------------------------------------------------------
Step "Abriendo navegador..."
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  APP EN MARCHA"                                -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  App web : http://localhost:3000"          -ForegroundColor White
Write-Host "  API     : http://localhost:8000/health"   -ForegroundColor White
Write-Host ""
Write-Host "  Para DETENER todo: doble clic en DETENER.bat" -ForegroundColor Gray
Write-Host ""
Read-Host "Pulsa ENTER para cerrar esta ventana (la app sigue corriendo)"
