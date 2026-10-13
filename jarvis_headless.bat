@echo off
setlocal
cd /d "%~dp0"
title J.A.R.V.I.S. - service

if not exist ".env" (
    echo .env file not found. Run install.bat first.
    pause
    exit /b 1
)

echo J.A.R.V.I.S. service: records, notifies and serves the page. Ctrl+C stops it.
echo To see the cameras: http://127.0.0.1:8765 or the Desktop shortcut.
echo.

uv run python -m jarvis --headless
set CODE=%errorlevel%

if not "%CODE%"=="0" (
    echo.
    echo The program ended with an error ^(code %CODE%^).
    pause
)
