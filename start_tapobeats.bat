@echo off
setlocal enabledelayedexpansion
:: TapoBeats Auto-Start Script
:: Starts Flask server + ngrok tunnel (single instance only)

cd /d "%~dp0"

:: ===== SINGLE INSTANCE CHECK =====
if exist ".tapobeats.lock" (
    set /p LOCKPID=<.tapobeats.lock
    tasklist /FI "PID eq !LOCKPID!" /NH 2>nul | findstr /I "python" >nul 2>&1
    if !errorlevel!==0 (
        echo TapoBeats is already running ^(PID !LOCKPID!^). Exiting.
        exit /b 0
    )
    del .tapobeats.lock >nul 2>&1
)

:: ===== LOAD CONFIG FROM .ENV =====
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="NGROK_DOMAIN" set NGROK_DOMAIN=%%b
)

if "!NGROK_DOMAIN!"=="" (
    echo ERROR: NGROK_DOMAIN not set in .env
    pause
    exit /b 1
)

:: ===== START SERVICES =====
call venv\Scripts\activate.bat

:: Start Flask server and save its PID via a wrapper
start /B cmd /c "python -m src.main serve & echo %^errorlevel%"

:: Wait for Flask to bind
timeout /t 3 /nobreak >nul

:: Capture the python PID listening on port 5000
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":5000.*LISTENING"') do (
    tasklist /FI "PID eq %%p" /NH 2>nul | findstr /I "python" >nul 2>&1
    if !errorlevel!==0 (
        echo %%p> .tapobeats.lock
        goto :start_ngrok
    )
)

:start_ngrok
:: Kill any stale ngrok, then start fresh
taskkill /F /IM ngrok.exe >nul 2>&1
start /B ngrok http 5000 --domain !NGROK_DOMAIN!

echo TapoBeats is running!
echo Flask: http://localhost:5000
endlocal
