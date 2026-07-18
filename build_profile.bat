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

%PYTHON_CMD% scripts\sync_ivrit_sheli.py --write
if errorlevel 1 goto :failed
%PYTHON_CMD% scripts\sync_novafit.py --write
if errorlevel 1 goto :failed
%PYTHON_CMD% scripts\sync_ivrit_sheli.py --check
if errorlevel 1 goto :failed
%PYTHON_CMD% scripts\sync_novafit.py --check
if errorlevel 1 goto :failed

%PYTHON_CMD% tools\profile\generate_signature_assets.py
if errorlevel 1 goto :failed
%PYTHON_CMD% tools\profile\generate_signature_assets.py --check
if errorlevel 1 goto :failed

%PYTHON_CMD% scripts\build_profile.py --mode compact --output README.md
if errorlevel 1 goto :failed
%PYTHON_CMD% scripts\build_profile.py --mode expanded --output README_EXPANDED.md
if errorlevel 1 goto :failed

%PYTHON_CMD% scripts\build_profile.py --mode compact --output README.md --check
if errorlevel 1 goto :failed
%PYTHON_CMD% scripts\build_profile.py --mode expanded --output README_EXPANDED.md --check
if errorlevel 1 goto :failed

%PYTHON_CMD% scripts\validate_profile.py --readme README.md --max-lines 300 --mode compact --check-localized
if errorlevel 1 goto :failed
%PYTHON_CMD% scripts\validate_profile.py --readme README_EXPANDED.md --max-lines 300 --mode expanded
if errorlevel 1 goto :failed

%PYTHON_CMD% -m compileall -q scripts tests tools\profile
if errorlevel 1 goto :failed
%PYTHON_CMD% -m doctest scripts\build_profile.py scripts\validate_profile.py tools\profile\generate_world_globe.py
if errorlevel 1 goto :failed
%PYTHON_CMD% -m unittest discover -s tests -v
if errorlevel 1 goto :failed
powershell -NoProfile -ExecutionPolicy Bypass -File tools\profile\verify-profile.ps1
if errorlevel 1 goto :failed

echo.
echo Compact and expanded profiles generated, synchronized and fully validated. READY
pause
exit /b 0

:failed
echo.
echo Profile generation failed. Review the message above.
pause
exit /b 1
