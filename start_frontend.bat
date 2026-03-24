@echo off
echo ============================================
echo  CAN BUS IDS - Starting Frontend Dashboard
echo ============================================
echo.

cd /d "%~dp0\frontend"
call npm run dev

pause
