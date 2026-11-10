@echo off
chcp 65001 >nul
title "CU-03 - Tests"
where uv >nul 2>nul
if %errorlevel% equ 0 (
    uv run --group dev pytest %*
    goto end
)
python -m pytest %*

:end
echo.
pause
