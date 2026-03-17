@echo off
:: TapoBeats Stop Script
:: Cleanly stops Flask server + ngrok tunnel

cd /d "%~dp0"

echo Stopping TapoBeats...

:: Kill ngrok
taskkill /F /IM ngrok.exe >nul 2>&1

:: Kill Flask using lock file PID
if exist ".tapobeats.lock" (
    set /p LOCKPID=<.tapobeats.lock
    taskkill /F /PID %LOCKPID% >nul 2>&1
    del .tapobeats.lock >nul 2>&1
)

:: Fallback: kill any python still on port 5000
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":5000.*LISTENING"') do (
    tasklist /FI "PID eq %%p" /NH 2>nul | findstr /I "python" >nul 2>&1
    if not errorlevel 1 taskkill /F /PID %%p >nul 2>&1
)

echo TapoBeats stopped.
