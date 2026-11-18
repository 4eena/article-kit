@echo off
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
py -3 web_app.py
if errorlevel 1 (
  where py >nul 2>&1
  if errorlevel 1 python web_app.py
)
pause
