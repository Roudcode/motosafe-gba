@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   MotoSafe GBA - Reiniciando (sin duplicar procesos)
echo ============================================
echo.
echo Busco que proceso tiene ocupados los puertos 8000 (backend) y 5175
echo (frontend), y SOLO cierro esos dos PID puntuales -- no toco ningun
echo otro proceso de la PC.

for %%P in (8000 5175) do (
    set "PID_PUERTO="
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr /r ":%%P[^0-9].*LISTENING"') do (
        set "PID_PUERTO=%%A"
    )
    if defined PID_PUERTO (
        echo Puerto %%P ocupado por PID !PID_PUERTO!, lo cierro...
        taskkill /PID !PID_PUERTO! /F >nul 2>nul
    ) else (
        echo Puerto %%P libre, nada que cerrar.
    )
)

echo.
echo Apagando Tailscale Funnel (si estaba activo)...
tailscale funnel 443 off >nul 2>nul

echo Esperando 2 segundos...
timeout /t 2 >nul

echo.
echo Volviendo a levantar la app...
call "%~dp0iniciar_app_tailscale.bat"
