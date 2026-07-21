@echo off
setlocal
echo.
echo.
echo  Rummikub - Start local development stack
echo.
echo.
echo This will open:
echo   1. Backend window
echo   2. Worker window
echo   3. Build + install app on connected phone
echo.
echo Make sure PostgreSQL, Redis and MinIO are already running.
echo Connect your phone with USB debugging enabled.
echo.
pause

start "Rummikub Backend" "%~dp0start-backend.bat"
timeout /t 3 /nobreak >nul
start "Rummikub Worker" "%~dp0start-worker.bat"
echo Waiting a few seconds for backend to start...
timeout /t 8 /nobreak >nul

powershell -ExecutionPolicy Bypass -File "%~dp0deploy-phone.ps1"
echo.
pause
