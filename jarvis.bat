@echo off
setlocal
cd /d "%~dp0"
title J.A.R.V.I.S.

if not exist ".env" (
    echo Arquivo .env nao encontrado. Rode install.bat primeiro.
    pause
    exit /b 1
)

uv run python -m jarvis
set CODIGO=%errorlevel%

if not "%CODIGO%"=="0" (
    echo.
    echo O programa terminou com erro ^(codigo %CODIGO%^).
    pause
)
