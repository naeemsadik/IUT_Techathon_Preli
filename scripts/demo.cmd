@echo off
REM ==============================================================================
REM  Office Energy Monitoring - Demo launcher (pure Windows batch, no PowerShell)
REM
REM  Starts backend, simulator, and dashboard each in their own console window.
REM
REM  Usage (from repo root):
REM
REM      scripts\demo.cmd             REM full stack (backend + simulator + dashboard)
REM      scripts\demo.cmd stop        REM kill everything started above
REM
REM ==============================================================================

setlocal EnableDelayedExpansion

REM Resolve repo root (this file lives in <repo>\scripts\)
set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "LOG_DIR=%REPO_ROOT%\logs_demo"
set "MARKER=%LOG_DIR%\.demo-pids.txt"

REM ---- argparse-lite: stop? ------------------------------------------------
if /I "%~1"=="stop" goto stop_action

REM ---- setup --------------------------------------------------------------
if not exist "%REPO_ROOT%\.venv\Scripts\python.exe" (
    echo [setup] Creating venv and installing requirements...
    cd /d "%REPO_ROOT%"
    python -m venv ".venv" || goto :error
    call ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)

if not exist "%REPO_ROOT%\backend\.env" (
    echo [setup] Creating backend\.env from example
    copy /Y "%REPO_ROOT%\backend\.env.example" "%REPO_ROOT%\backend\.env" >nul
)

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "PY=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [error] Python interpreter not found at: %PY%
    echo         Please run: python -m venv .venv ^&^& .venv\Scripts\python -m pip install -r requirements.txt
    exit /b 1
)

REM ---- launch each component in its own window ----------------------------
echo [start] Backend on http://127.0.0.1:8000
start "Office-Energy / Backend" /B cmd /c "set PYTHONUNBUFFERED=1 && cd /d "%REPO_ROOT%" && "%PY%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 1>"%LOG_DIR%\backend.out.log" 2>"%LOG_DIR%\backend.err.log""

REM Give the backend a moment to bind to port 8000 before the simulator starts.
ping -n 3 127.0.0.1 >nul

echo [start] Simulator (15 devices, staggered 3s/5s/7s)
start "Office-Energy / Simulator" /B cmd /c "set PYTHONUNBUFFERED=1 && cd /d "%REPO_ROOT%" && "%PY%" -m simulator.simulator 1>"%LOG_DIR%\simulator.out.log" 2>"%LOG_DIR%\simulator.err.log""

echo [start] Dashboard on http://127.0.0.1:5500
start "Office-Energy / Dashboard" /B cmd /c "set PYTHONUNBUFFERED=1 && cd /d "%REPO_ROOT%" && "%PY%" -m http.server 5500 --directory dashboard 1>"%LOG_DIR%\dashboard.out.log" 2>"%LOG_DIR%\dashboard.err.log""

echo.
echo ============================================================
echo Demo stack is up.
echo   Backend:   http://127.0.0.1:8000/docs
echo   Dashboard: http://127.0.0.1:5500
echo   Logs:      %LOG_DIR%\
echo.
echo To stop everything:
echo   scripts\demo.cmd stop
echo ============================================================
echo.
exit /b 0

:stop_action
REM ---- tear-down: kill processes by title ---------------------------------
echo [stop] Killing backend, simulator, dashboard windows...
taskkill /FI "WINDOWTITLE eq Office-Energy / Backend*"   /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Office-Energy / Simulator*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Office-Energy / Dashboard*" /T /F >nul 2>&1
REM Belt-and-suspenders: also kill any orphaned uvicorn / simulator / http.server
taskkill /IM uvicorn.exe /T /F >nul 2>&1
taskkill /IM python.exe /FI "WINDOWTITLE eq Office-Energy*" /T /F >nul 2>&1
if exist "%MARKER%" del /F /Q "%MARKER%"
echo [stop] Done.
exit /b 0

:error
echo [error] Setup failed. Please ensure Python is installed and on PATH.
exit /b 1