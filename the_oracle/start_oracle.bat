@echo off
REM THE ORACLE - Continuous Runner for Windows
REM Runs monitor in background using pythonw (no console window)

echo ========================================
echo THE ORACLE - Starting Continuous Mode
echo ========================================
echo.

set ORACLE_DIR=%~dp0
cd /d "%ORACLE_DIR%"

REM Check if already running
tasklist /FI "IMAGENAME eq pythonw.exe" /FI "WINDOWTITLE eq *oracle*" 2>nul | find /I "pythonw.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] Oracle monitor already running!
    echo Use: taskkill /F /IM pythonw.exe  to stop
    pause
    exit /b 1
)

REM Create log directory if not exists
if not exist "output" mkdir output

REM Start monitor in background (no console window)
echo Starting Oracle Monitor...
echo Logs: the_oracle/output/monitor.log
echo.

start /B "" pythonw.exe monitor_continuous.py

echo [OK] Oracle started in background
echo.
echo To stop: taskkill /F /IM pythonw.exe
echo To view logs: type output/monitor.log
echo.
pause
