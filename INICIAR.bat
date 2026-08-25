@echo off
title PDF Suite
cd /d "%~dp0backend"
start "PDF-API" /min "" python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
cd /d "%~dp0frontend"
start "PDF-Web" /min "" cmd /c "npm run dev"
start "" /min cmd /c "ping 127.0.0.1 -n 36 >nul & start http://localhost:3000"
exit
