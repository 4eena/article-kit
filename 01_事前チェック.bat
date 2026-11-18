@echo off
cd /d "%~dp0"
py -3 preflight.py
echo.
echo Press any key to close...
pause >nul
