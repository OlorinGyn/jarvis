@echo off
setlocal
cd /d "%~dp0"
title J.A.R.V.I.S. installation

echo ============================================
echo   J.A.R.V.I.S. - installation
echo ============================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [1/7] uv not found. Installing it...
    winget install --id=astral-sh.uv -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo.
        echo ERROR: could not install uv automatically.
        echo Install it by hand from https://docs.astral.sh/uv/ and run this script again.
        pause
        exit /b 1
    )
    echo.
    echo uv is installed, but the PATH only updates in a new window.
    echo CLOSE this window and run install.bat again.
    pause
    exit /b 0
) else (
    echo [1/7] uv found.
)

echo [2/7] Checking the Visual C++ Redistributable...
echo       ^(OpenCV depends on it and does not bundle it^)
winget install --id=Microsoft.VCRedist.2015+.x64 -e --accept-source-agreements --accept-package-agreements >nul 2>&1
echo       done.

echo [3/7] The official Python, signed by the Python Software Foundation...
echo       ^(Windows 11's Smart App Control blocks an unsigned Python^)
winget install --id=Python.Python.3.14 -e --scope user --accept-source-agreements --accept-package-agreements --silent >nul 2>&1
echo       done.

echo [4/7] Installing dependencies ^(may take a while the first time^)...
uv sync
if errorlevel 1 (
    echo.
    echo ERROR: could not install the dependencies.
    echo If the message above says WinError 4551 or Failed to spawn: python,
    echo Smart App Control blocked an unsigned Python: docs\INSTALL.md section 1.2.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\check_python.ps1" -Path "%~dp0.venv\Scripts\python.exe"
if errorlevel 1 (
    echo.
    echo uv is using a Python that is not the official one, usually because
    echo step 3 failed. Install it by hand, recreate .venv and run this
    echo script again: docs\INSTALL.md section 1.2.
    pause
    exit /b 1
)

echo [5/7] Downloading vision models ^(~340 MB^)...
uv run python -c "from jarvis import people, faces; people.ensure_model(); faces.ensure_models(); print('      models ready')"
if errorlevel 1 (
    echo.
    echo ERROR: could not prepare the models.
    echo.
    echo If the message above mentions a DLL or WinError 1114, the
    echo Visual C++ Redistributable is missing:
    echo.
    echo    winget install --id Microsoft.VCRedist.2015+.x64 -e
    echo.
    echo Any other error: check the internet connection.
    pause
    exit /b 1
)

echo [6/7] Desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\create_shortcut.ps1"

echo [7/7] Camera configuration...
if exist ".env" (
    echo      .env already exists, kept as it is.
) else (
    copy ".env.example" ".env" >nul
    echo      .env created from the template.
    echo.
    echo      ATTENTION: edit the .env file with your cameras' IP
    echo      and credentials before starting.
    echo.
    notepad ".env"
)

echo.
echo ============================================
echo   Installation finished.
echo   Use jarvis.bat to start the program.
echo ============================================
pause
