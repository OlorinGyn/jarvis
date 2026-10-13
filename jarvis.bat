@echo off
setlocal
cd /d "%~dp0"
title J.A.R.V.I.S.

if not exist ".env" (
    echo .env file not found. Run install.bat first.
    pause
    exit /b 1
)

uv run python -m jarvis
set CODE=%errorlevel%

if not "%CODE%"=="0" (
    echo.
    echo The program ended with an error ^(code %CODE%^).
    pause
)
