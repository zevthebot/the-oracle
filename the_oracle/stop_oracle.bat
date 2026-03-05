@echo off
REM Stop THE ORACLE Monitor

echo Stopping Oracle Monitor...
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *oracle*" 2>nul

echo [OK] Oracle stopped
pause
