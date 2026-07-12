@echo off
setlocal
cd /d "%~dp0..\backend"

echo [Backend] Checking Python 3.12 virtual environment...
if not exist ".venv\Scripts\activate.bat" (
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo ERROR: Python 3.12 is required. Install it or fix the py launcher.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if not exist ".env" copy .env.example .env

echo.
echo [Backend] Starting API server at http://0.0.0.0:8000
echo [Backend] Docs: http://localhost:8000/docs
echo [Backend] Leave this window open.
echo.
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
pause
