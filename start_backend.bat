@echo off
setlocal EnableExtensions

echo ============================================
echo  CAN BUS IDS - Starting Backend API
echo ============================================
echo.

cd /d "%~dp0"
set "ROOT_DIR=%CD%"

set "REPORTS_DIR=%ROOT_DIR%\reports"
if not exist "%REPORTS_DIR%" (
	mkdir "%REPORTS_DIR%"
)

set "PYTHON_CMD="

if exist "%ROOT_DIR%\venv\Scripts\python.exe" (
	set "PYTHON_CMD=\"%ROOT_DIR%\venv\Scripts\python.exe\""
) else (
	where py >nul 2>nul
	if not errorlevel 1 (
		set "PYTHON_CMD=py -3"
	) else (
		where python >nul 2>nul
		if not errorlevel 1 (
			set "PYTHON_CMD=python"
		)
	)
)

if "%PYTHON_CMD%"=="" (
	echo [ERROR] Python was not found on this machine.
	echo [HINT] Install Python 3.10+ and re-run this script.
	goto :end
)

echo [INFO] Using Python command: %PYTHON_CMD%

%PYTHON_CMD% -c "import fastapi, uvicorn" >nul 2>nul
if errorlevel 1 (
	echo [ERROR] Required backend packages are missing.
	echo [HINT] Run the following setup commands first:
	echo        %PYTHON_CMD% -m venv venv
	echo        venv\Scripts\activate
	echo        %PYTHON_CMD% -m pip install -r requirements.txt
	goto :end
)

echo [INFO] Starting API at http://localhost:8000
%PYTHON_CMD% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

:end
echo.
pause
endlocal
