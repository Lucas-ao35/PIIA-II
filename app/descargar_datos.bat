@echo off
chcp 65001 >nul
title "CU-03 - Descarga de Datasets Clinicos"
echo ======================================================================
echo    CU-03 PIIA2 - Descarga de Datasets Clinicos (PharmaCoNER)
echo ======================================================================
echo.

where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [*] Ejecutando descarga con uv...
    uv run python scripts\download_datasets.py %*
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [*] Ejecutando descarga con Python...
    python scripts\download_datasets.py %*
    goto end
)

echo [!] Error: No se encontro Python ni uv en el sistema.
echo     Instala Python 3.11+ o uv para continuar.

:end
echo.
pause
