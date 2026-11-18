@echo off
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag a generated ZIP onto this BAT file.
) else (
  py -3 verify_kit.py "%~1"
)
echo.
pause
