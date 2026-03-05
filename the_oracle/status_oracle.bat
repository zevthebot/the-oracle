@echo off
REM Check Oracle status

echo Checking Oracle Monitor status...
echo.

tasklist /FI "IMAGENAME eq pythonw.exe" /FI "WINDOWTITLE eq *oracle*" 2>nul | find /I "pythonw.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo [RUNNING] Oracle monitor is active
    echo.
    echo Recent log entries:
    type the_oracle\output\monitor.log 2>nul | tail -20
) else (
    echo [STOPPED] Oracle monitor is not running
    echo.
    echo To start: run start_oracle.bat
)

echo.
pause
