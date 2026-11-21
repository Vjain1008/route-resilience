@echo off
title Route Resilience - Interactive Web Trial Server
cd /d "%~dp0"

echo ======================================================================
echo ROUTE RESILIENCE: 3D NON-STOP FLOW & AERIAL REPORT GENERATOR
echo ======================================================================
echo.

set "PY_BIN="

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
) else (
    where py >nul 2>&1 && set "PY_BIN=py"
    if not defined PY_BIN (
        where python >nul 2>&1 && set "PY_BIN=python"
    )
)

if not defined PY_BIN (
    echo [ERROR] Python 3 not found.
    echo Please install Python 3.9+ or run with your full python.exe path.
    pause
    exit /b 1
)

echo Using Python: %PY_BIN%
echo.
echo [1/2] Opening browser at http://localhost:8000 ...
start "" http://localhost:8000

echo [2/2] Launching FastAPI Web Application...
echo Press Ctrl+C to stop the server when done.
echo.

"%PY_BIN%" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [SERVER STOPPED OR FAILED TO START]
    pause
)
