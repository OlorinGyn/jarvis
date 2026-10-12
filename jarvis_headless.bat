@echo off
setlocal
cd /d "%~dp0"
title J.A.R.V.I.S. - servico

if not exist ".env" (
    echo Arquivo .env nao encontrado. Rode install.bat primeiro.
    pause
    exit /b 1
)

echo Servico do J.A.R.V.I.S.: grava, avisa e serve a pagina. Ctrl+C encerra.
echo Para ver as cameras: http://127.0.0.1:8765 ou o atalho da Area de Trabalho.
echo.

uv run python -m jarvis --sem-janela
set CODIGO=%errorlevel%

if not "%CODIGO%"=="0" (
    echo.
    echo O programa terminou com erro ^(codigo %CODIGO%^).
    pause
)
