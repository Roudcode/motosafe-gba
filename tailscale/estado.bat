@echo off
rem Estado rapido del acceso publico de MotoSafe (SES-085). No reinicia nada:
rem la tarea MotoSafe-Vigilancia es la que reinicia lo que falle.
setlocal
echo ============================================
echo   MotoSafe GBA - Estado
echo ============================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0vigilancia.ps1" -SoloEstado
echo.
echo Ultimas revisiones automaticas (logs\vigilancia):
for /f "delims=" %%L in ('dir /b /o-n "%~dp0..\logs\vigilancia\vigilancia_*.log" 2^>nul') do (
    powershell -NoProfile -Command "Get-Content -Path '%~dp0..\logs\vigilancia\%%L' -Tail 3"
    goto :fin
)
echo   (todavia no hay registros)
:fin
echo.
pause
