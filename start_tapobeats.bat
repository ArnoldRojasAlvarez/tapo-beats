@echo off
:: TapoBeats Auto-Start Script
:: Starts Flask server + ngrok tunnel

cd /d "%~dp0"

:: Load ngrok domain from .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="NGROK_DOMAIN" set NGROK_DOMAIN=%%b
)

if "%NGROK_DOMAIN%"=="" (
    echo ERROR: NGROK_DOMAIN not set in .env
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start Flask server in background
start /B python -m src.main serve

:: Wait for Flask to be ready
timeout /t 3 /nobreak >nul

:: Start ngrok with static domain from .env
start /B ngrok http 5000 --domain %NGROK_DOMAIN%

echo TapoBeats is running!
echo Flask: http://localhost:5000
echo Press Ctrl+C to stop
pause >nul
