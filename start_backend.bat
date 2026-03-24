@echo off
echo ============================================
echo  CAN BUS IDS - Starting Backend API
echo ============================================
echo.

cd /d "%~dp0"
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000

pause
