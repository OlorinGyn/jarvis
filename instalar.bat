@echo off
setlocal
cd /d "%~dp0"
title Instalacao do J.A.R.V.I.S.

echo ============================================
echo   J.A.R.V.I.S. - instalacao
echo ============================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [1/5] uv nao encontrado. Instalando...
    winget install --id=astral-sh.uv -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo.
        echo ERRO: nao consegui instalar o uv automaticamente.
        echo Instale manualmente em https://docs.astral.sh/uv/ e rode este script de novo.
        pause
        exit /b 1
    )
    echo.
    echo O uv foi instalado, mas o PATH so atualiza numa janela nova.
    echo FECHE esta janela e rode instalar.bat novamente.
    pause
    exit /b 0
) else (
    echo [1/5] uv encontrado.
)

echo [2/5] Verificando o Visual C++ Redistributable...
echo       ^(o PyTorch depende dele e nao o empacota^)
winget install --id=Microsoft.VCRedist.2015+.x64 -e --accept-source-agreements --accept-package-agreements >nul 2>&1
echo       pronto.

echo [3/5] Instalando dependencias ^(pode demorar na primeira vez^)...
uv sync
if errorlevel 1 (
    echo.
    echo ERRO: falha ao instalar as dependencias.
    pause
    exit /b 1
)

echo [4/5] Baixando modelos de visao...
uv run python -c "import faces; faces.ensure_models()"
if errorlevel 1 (
    echo.
    echo ERRO: falha ao baixar os modelos de rosto.
    echo Verifique a conexao com a internet e rode de novo.
    pause
    exit /b 1
)

uv run python -c "from ultralytics import YOLO; YOLO('yolo11s.pt'); print('      modelos prontos')"
if errorlevel 1 (
    echo.
    echo ERRO: o PyTorch nao carregou.
    echo.
    echo Se a mensagem acima menciona DLL, WinError 1114 ou c10.dll,
    echo falta o Visual C++ Redistributable. Instale manualmente:
    echo.
    echo    winget install --id Microsoft.VCRedist.2015+.x64 -e
    echo.
    echo Ou baixe em: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo Depois reinicie o computador e rode instalar.bat de novo.
    pause
    exit /b 1
)

echo [5/5] Configuracao das cameras...
if exist ".env" (
    echo      .env ja existe, mantido como esta.
) else (
    copy ".env.example" ".env" >nul
    echo      .env criado a partir do modelo.
    echo.
    echo      ATENCAO: edite o arquivo .env com o IP e as credenciais
    echo      das suas cameras antes de iniciar.
    echo.
    notepad ".env"
)

echo.
echo ============================================
echo   Instalacao concluida.
echo   Use jarvis.bat para iniciar o programa.
echo ============================================
pause
