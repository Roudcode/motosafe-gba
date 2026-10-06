@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Tailscale Funnel
echo ============================================
echo.
echo Publica el frontend (puerto 5175, HTTPS con certificado autofirmado)
echo como unico punto de entrada publico. El backend (8000) NO se expone
echo directo a internet: Vite le hace de proxy interno via /api (ver
echo frontend/vite.config.js), igual que ya pasa en desarrollo local.
echo.
echo Requisitos antes de correr esto (una sola vez):
echo  1) Tailscale instalado y con sesion iniciada en esta PC.
echo  2) "Funnel" habilitado para este dispositivo en
echo     https://login.tailscale.com/admin/machines
echo     (entra a "%COMPUTERNAME%" -^> Funnel -^> habilitar).
echo.
echo Puerto publico FIJO para MotoSafe: 443 (explicito a proposito). Si en
echo esta PC corre otro proyecto con su propio Funnel (ej: Nexo en 8443),
echo cada uno queda en su propio puerto publico y no se pisan -- Tailscale
echo Funnel soporta hasta 3 puertos publicos por dispositivo: 443, 8443 y
echo 10000. Ver tailscale\README.md, seccion "Varios proyectos en la
echo misma PC".
echo.

tailscale funnel --bg --https=443 https+insecure://127.0.0.1:5175
if errorlevel 1 (
    echo.
    echo ERROR al activar Funnel. Revisa los dos requisitos de arriba.
    echo Si el comando da error de sintaxis, tu version de Tailscale puede
    echo usar otra forma -- corre "tailscale funnel --help" y fijate la
    echo sintaxis exacta para publicar un backend https con certificado
    echo autofirmado ^(suele ser el esquema "https+insecure://"^).
    pause
    exit /b 1
)

echo.
echo Funnel activo en segundo plano. Guardando el estado...
tailscale funnel status > "%~dp0_funnel_status.txt" 2>&1
type "%~dp0_funnel_status.txt"

rem Mejor esfuerzo para extraer la URL publica del status. Si no aparece
rem ninguna linea con "https://", abri _funnel_status.txt a mano y copiala.
set "URL_ENCONTRADA="
for /f "tokens=*" %%A in ('findstr /r "https://[a-zA-Z0-9.-]*\.ts\.net" "%~dp0_funnel_status.txt"') do (
    if not defined URL_ENCONTRADA (
        for %%B in (%%A) do (
            echo %%B | findstr /b "https://" >nul && set "URL_ENCONTRADA=%%B"
        )
    )
)

if defined URL_ENCONTRADA (
    echo !URL_ENCONTRADA! > "%~dp0public_url.txt"
    echo.
    echo URL publica: !URL_ENCONTRADA!
    echo Guardada en tailscale\public_url.txt
    echo Pegala como PUBLIC_URL en backend\.env si todavia no lo hiciste.
) else (
    echo.
    echo No pude extraer la URL automaticamente. Mira el archivo
    echo tailscale\_funnel_status.txt y copia a mano la que empiece con
    echo https:// y termine en .ts.net
)
echo.
pause
