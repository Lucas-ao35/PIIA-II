@echo off
chcp 65001 >nul
title "CU-03 - Visualizador Clinico (Streamlit)"
echo ======================================================================
echo    CU-03 PIIA2 - Lanzador de la Aplicacion Web (Streamlit)
echo ======================================================================
echo.

where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [*] Detectado gestor uv. Iniciando Streamlit con uv...
    uv run streamlit run app.py
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [*] uv no esta instalado. Iniciando Streamlit con Python del sistema...
    python -m streamlit run app.py
    if %errorlevel% neq 0 (
        echo.
        echo [!] Ocurrio un error al ejecutar Streamlit.
        echo [i] Si falta algun paquete, ejecuta:
        echo        pip install -r requirements.txt
    )
    goto end
)

echo [!] Error: No se encontro ni 'uv' ni 'python' en el PATH del sistema.
echo     Instala Python 3.11+ o uv (https://docs.astral.sh/uv/) para continuar.

:end
echo.
pause
