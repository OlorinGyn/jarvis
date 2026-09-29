@echo off
setlocal
cd /d "%~dp0"
title J.A.R.V.I.S.

if not exist ".env" (
    echo Arquivo .env nao encontrado. Rode instalar.bat primeiro.
    pause
    exit /b 1
)

uv run cameras.py
set CODIGO=%errorlevel%

if not "%CODIGO%"=="0" (
    echo.
    echo O programa terminou com erro ^(codigo %CODIGO%^).
    pause
)
