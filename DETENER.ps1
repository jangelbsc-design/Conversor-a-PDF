# ============================================================
#  PDF Suite Local - DETENER
#  Cierra el backend y el frontend arrancados con INICIAR.bat
# ============================================================
#requires -Version 5.1
$ErrorActionPreference = "SilentlyContinue"

$LogsDir = Join-Path $PSScriptRoot "logs"
$Stopped = 0

foreach ($name in @("backend", "frontend")) {
    $pidFile = Join-Path $LogsDir "$name.pid"
    if (Test-Path $pidFile) {
        $procId = (Get-Content $pidFile -Raw).Trim()
        if ($procId) {
            Write-Host "Deteniendo $name (PID $procId)..."
            taskkill /PID $procId /T /F | Out-Null
            if ($LASTEXITCODE -eq 0) { $Stopped++ }
            Remove-Item $pidFile -Force
        }
    }
}

# Red de seguridad: matar lo que quede escuchando en los puertos
foreach ($port in @(8000, 3000)) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($procId in ($conn.OwningProcess | Sort-Object -Unique)) {
        Write-Host "Liberando puerto $port (PID $procId)..."
        taskkill /PID $procId /T /F | Out-Null
        if ($LASTEXITCODE -eq 0) { $Stopped++ }
    }
}

Write-Host ""
if ($Stopped -gt 0) { Write-Host "Listo: procesos detenidos." -ForegroundColor Green }
else { Write-Host "No habia procesos de la app en marcha." -ForegroundColor Yellow }
Read-Host "Pulsa ENTER para cerrar"
