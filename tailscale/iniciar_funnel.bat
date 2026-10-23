@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Tailscale Funnel
echo ============================================
echo.
echo Publica el frontend (puerto 5175, HTTP plano -- Funnel pone el unico
echo HTTPS real de cara a internet, con certificado valido, no el
echo autofirmado de Vite). El backend (8000) NO se expone directo a
echo internet: Vite le hace de proxy interno via /api (ver
echo frontend/vite.config.js), igual que ya pasa en desarrollo local.
echo.
echo Cambiado en SES-164: antes el proxy interno era https+insecure hacia
echo el certificado autofirmado de Vite, y esa doble capa de TLS disparaba
echo una renegociacion que Chrome rechaza por seguridad (ERR_SSL_PROTOCOL_ERROR
echo en el celular, mientras PC/Safari la toleraban). Con el frontend en HTTP
echo plano (ver MOTOSAFE_SIN_HTTPS=1 en iniciar_app_tailscale.bat) esa capa
echo interna desaparece -- Funnel es el unico que termina TLS.
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

tailscale funnel --bg --https=443 http://127.0.0.1:5175
if errorlevel 1 (
    echo.
    echo ERROR al activar Funnel. Revisa los dos requisitos de arriba.
    echo Si el comando da error de sintaxis, tu version de Tailscale puede
    echo usar otra forma -- corre "tailscale funnel --help" y fijate la
    echo sintaxis exacta para publicar un backend https con certificado
    echo http plano ^(suele ser el esquema "http://"^).
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
