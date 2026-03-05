@echo off
echo ============================================
echo THE ORACLE - Monitor and Auto-Restart
echo ============================================
echo.
echo Starting monitoring check...
echo.

cd C:\Users\Claw\.openclaw\workspace
python the_oracle\monitor.py

echo.
echo ============================================
echo Check completed at: %date% %time%
echo ============================================
