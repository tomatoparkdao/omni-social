@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%~dp0"
if not exist "%ROOT%.venv\Scripts\python.exe" (
  echo Python virtual environment not found. Create it with: python -m venv .venv
  exit /b 1
)
if not exist "%ROOT%sau_frontend\node_modules" (
  echo Installing frontend dependencies...
  pushd "%ROOT%sau_frontend" && npm install || (popd & exit /b 1)
  popd
)
start "OmniSocial Backend" cmd /k "cd /d "%ROOT%" && .venv\Scripts\python.exe sau_backend.py"
start "OmniSocial Frontend" cmd /k "cd /d "%ROOT%sau_frontend" && npm run dev -- --host 127.0.0.1"
powershell -NoProfile -Command "Start-Sleep -Seconds 4"
start "" http://127.0.0.1:5173
echo OmniSocial: http://127.0.0.1:5173
endlocal
