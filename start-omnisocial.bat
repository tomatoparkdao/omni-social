@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo OmniSocial virtual environment is missing.
  pause
  exit /b 1
)
rem Local development only: auth is explicitly opted in and bound to loopback.
rem Production deployments must use OMNISOCIAL_AUTH_MODE=production (see compose.yaml).
set "OMNISOCIAL_AUTH_MODE=local_dev"
set "OMNISOCIAL_ENV=local"
set "OMNISOCIAL_BIND_HOST=127.0.0.1"
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\omnisocial_service.py" start
if errorlevel 1 (
  echo.
  echo OmniSocial failed to start. Check logs\backend-dev.log for details.
  pause
)
exit /b %ERRORLEVEL%
