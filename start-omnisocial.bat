@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo OmniSocial virtual environment is missing.
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\omnisocial_service.py" start
exit /b %ERRORLEVEL%
