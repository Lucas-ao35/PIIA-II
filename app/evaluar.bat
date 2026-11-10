@echo off
chcp 65001 >nul
title "CU-03 - Evaluacion del pipeline"
echo ======================================================================
echo    CU-03 PIIA2 - Evaluacion reproducible (por defecto: train -^> dev)
echo    Argumentos opcionales, p. ej.:  evaluar.bat --min-precision 0.3
echo ======================================================================
echo.

where uv >nul 2>nul
if %errorlevel% equ 0 (
    uv run python scripts\evaluate.py %*
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python scripts\evaluate.py %*
    goto end
)

echo [!] Error: No se encontro Python ni uv en el sistema.

:end
echo.
pause
