@echo off
echo ============================================
echo   MotoSafe GBA - Apagando Tailscale Funnel
echo ============================================
echo.

tailscale funnel 443 off
if errorlevel 1 (
    echo.
    echo Si dio error de sintaxis, tu version de Tailscale puede pedir otra
    echo forma del comando. Corre "tailscale funnel status" para ver el
    echo puerto publico real en uso y "tailscale funnel --help" para la
    echo sintaxis exacta de tu version.
)

echo.
echo Estado actual:
tailscale funnel status
echo.
echo El backend y el frontend locales siguen corriendo -- esto solo apaga
echo la publicacion a internet. Para pararlos tambien, cerra las ventanas
echo o usa el Administrador de tareas.
pause
