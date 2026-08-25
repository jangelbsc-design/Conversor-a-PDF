# PDF Suite - DETENER (silencioso, sin preguntas)
#requires -Version 5.1
$ErrorActionPreference = "SilentlyContinue"

$pidDir = Join-Path $PSScriptRoot "logs"

foreach ($name in @("backend", "frontend")) {
    $pidFile = Join-Path $pidDir "$name.pid"
    if (Test-Path $pidFile) {
        $pidVal = (Get-Content $pidFile -Raw).Trim()
        if ($pidVal) { taskkill /PID $pidVal /T /F 2>$null | Out-Null }
        Remove-Item $pidFile -Force
    }
}

foreach ($port in @(8000, 3000)) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { taskkill /PID $_ /T /F 2>$null | Out-Null }
}
exit 0
