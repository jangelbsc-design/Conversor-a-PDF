# ============================================================
#  PDF Suite Local - INICIAR
#  Doble clic -> la app se abre. Sin ventanas visibles.
#  Si ya esta corriendo -> solo abre el navegador.
# ============================================================
#requires -Version 5.1
$ErrorActionPreference = "SilentlyContinue"

$Root     = $PSScriptRoot
$LogsDir  = Join-Path $Root "logs"
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

function Test-Url($url) {
    try { return (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200 }
    catch { return $false }
}
function Aviso($msg) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($msg, "PDF Suite", 0, 48) | Out-Null
}

# --- Ya esta corriendo? -> navegador y listo ---
if ((Test-Url "http://127.0.0.1:8000/health") -and (Test-Url "http://localhost:3000")) {
    Start-Process "http://localhost:3000"; exit 0
}

# --- Limpiar restos ---
foreach ($p in @(8000, 3000)) {
    Get-NetTCPConnection -LocalPort $p -State Listen -EA SilentlyContinue |
        Select-Object -Expand OwningProcess -Unique |
        ForEach-Object { taskkill /PID $_ /T /F 2>$null | Out-Null }
}
Start-Sleep -Seconds 1

# --- Backend ---
$Py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = (Get-Command python -EA SilentlyContinue).Source }
if (-not $Py) { Aviso "No se encontro Python. Ejecuta PREPARAR.bat."; exit 1 }

Start-Process -FilePath $Py `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000","--log-file","$LogsDir\uvicorn.log" `
    -WorkingDirectory $Backend -WindowStyle Hidden | Out-Null

$ok = $false
for ($i=0; $i -lt 40; $i++) { Start-Sleep 1; if (Test-Url "http://127.0.0.1:8000/health") { $ok=$true; break } }
if (-not $ok) { Aviso "El servicio interno no arranco. Revisa logs\uvicorn.log"; exit 1 }

# --- Frontend ---
$Npm = (Get-Command npm.cmd -EA SilentlyContinue).Source
if (-not $Npm) {
    $nd = Get-ChildItem -Directory (Join-Path $Root "tools") -Filter "node-*" -EA SilentlyContinue | Select-Object -First 1
    if ($nd) { $Npm = Join-Path $nd.FullName "npm.cmd" }
}
if (-not $Npm) { Aviso "No se encontro Node.js. Ejecuta PREPARAR.bat."; exit 1 }

Start-Process -FilePath $Npm `
    -ArgumentList "run","dev" `
    -WorkingDirectory $Frontend -WindowStyle Hidden | Out-Null

for ($i=0; $i -lt 120; $i++) { Start-Sleep 1; if (Test-Url "http://localhost:3000") { break } }

# --- Abrir app ---
Start-Process "http://localhost:3000"
exit 0
