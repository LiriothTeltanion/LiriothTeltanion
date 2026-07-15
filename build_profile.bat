@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
  echo Python 3 was not found.
  pause
  exit /b 1
)

%PYTHON_CMD% scripts\build_profile.py --mode compact --output README.md
if errorlevel 1 goto :failed
%PYTHON_CMD% scripts\validate_profile.py --readme README.md --max-lines 300
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File tools\profile\verify-profile.ps1
if errorlevel 1 goto :failed

echo.
echo Profile README generated and validated. READY
pause
exit /b 0

:failed
echo.
echo Profile generation failed. Review the message above.
pause
exit /b 1
