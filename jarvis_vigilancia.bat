@echo off
setlocal
cd /d "%~dp0"
title J.A.R.V.I.S. - vigilancia sem janela

if not exist ".env" (
    echo Arquivo .env nao encontrado. Rode instalar.bat primeiro.
    pause
    exit /b 1
)

echo Gravando e avisando sem abrir janela. Ctrl+C encerra.
echo Para ver as cameras, use jarvis.bat.
echo.

uv run python -m jarvis --sem-janela
set CODIGO=%errorlevel%

if not "%CODIGO%"=="0" (
    echo.
    echo O programa terminou com erro ^(codigo %CODIGO%^).
    pause
)
