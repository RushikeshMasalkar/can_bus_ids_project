@echo off
setlocal EnableExtensions

echo ============================================
echo  CAN BUS IDS - Starting Frontend Dashboard
echo ============================================
echo.

cd /d "%~dp0\frontend"

where npm >nul 2>nul
if errorlevel 1 (
	echo [ERROR] npm was not found on this machine.
	echo [HINT] Install Node.js 18+ and re-run this script.
	goto :end
)

if not exist "node_modules" (
	echo [INFO] node_modules not found. Running npm install...
	call npm install
	if errorlevel 1 (
		echo [ERROR] npm install failed.
		goto :end
	)
)

echo [INFO] Starting frontend at http://localhost:3000
call npm run dev

:end
echo.
pause
endlocal
