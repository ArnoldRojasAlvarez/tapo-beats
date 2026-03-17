@echo off
:: TapoBeats Auto-Start Script
:: Starts Flask server + ngrok tunnel

cd /d "%~dp0"

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Start Flask server in background
start /B python -m src.main serve

:: Wait for Flask to be ready
timeout /t 3 /nobreak >nul

:: Start ngrok with static domain (URL never changes)
start /B ngrok http 5000 --domain YOUR_NGROK_DOMAIN_HERE

echo TapoBeats is running!
echo Flask: http://localhost:5000
echo Press Ctrl+C to stop
pause >nul
