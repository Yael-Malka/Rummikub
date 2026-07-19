@echo off
setlocal
cd /d "%~dp0..\worker"
set "PYTHONPATH=%~dp0..\worker"

echo [Worker] Checking Python 3.12 virtual environment...
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
echo [Worker] PYTHONPATH=%PYTHONPATH%
echo [Worker] Starting Celery. Leave this window open.
echo.
celery -A src.celery_app worker --loglevel=info --pool=solo
pause
