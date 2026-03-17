@echo off
:: Installs TapoBeats to run automatically on Windows startup
:: Run this script once as Administrator

echo Installing TapoBeats auto-start...

:: Create a scheduled task that runs at user logon
schtasks /create /tn "TapoBeats" /tr "wscript.exe \"%~dp0start_silent.vbs\"" /sc onlogon /rl highest /f

if %errorlevel% equ 0 (
    echo.
    echo TapoBeats will now start automatically when you log in.
    echo To remove: schtasks /delete /tn "TapoBeats" /f
) else (
    echo.
    echo Failed. Try running this script as Administrator.
)

pause
