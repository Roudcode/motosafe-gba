@echo off
setlocal

echo ============================================
echo   MotoSafe GBA - Watchdog (mantener activa)
echo ============================================
echo.
echo Chequea el backend cada 60 segundos. Si no responde, reinicia toda la
echo app (Docker + Backend + Frontend + Funnel) via reiniciar_app.bat.
echo Dejar esta ventana abierta (minimizada esta bien). Cerrarla corta solo
echo el watchdog, no la app en si.
echo.

:loop
curl -s -o nul http://127.0.0.1:8000/health
if errorlevel 1 (
    echo [%date% %time%] Backend no responde. Reiniciando...
    call "%~dp0reiniciar_app.bat"
) else (
    echo [%date% %time%] OK
)
timeout /t 60 >nul
goto loop
