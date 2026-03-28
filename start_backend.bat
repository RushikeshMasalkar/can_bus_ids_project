@echo off
echo ============================================
echo  CAN BUS IDS - Starting Backend API
echo ============================================
echo.

cd /d "%~dp0"

set "REPORTS_DIR=%~dp0reports"
if not exist "%REPORTS_DIR%" (
	mkdir "%REPORTS_DIR%"
)

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

pause
