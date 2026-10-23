@echo off
setlocal
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5409 .*LISTENING"') do taskkill /PID %%P /T /F >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173 .*LISTENING"') do taskkill /PID %%P /T /F >nul 2>&1
echo OmniSocial services stopped if they were running.
endlocal
