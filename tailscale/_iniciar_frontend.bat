@echo off
setlocal
cd /d "%~dp0..\frontend"

rem MOTOSAFE_SIN_HTTPS=1 hace que vite preview sirva en HTTP plano (Funnel
rem pone el unico TLS real de cara a internet -- ver SES-164). Puesto en su
rem propia linea, no encadenado con "&&" en el mismo renglon que el comando
rem siguiente: cmd.exe no propaga de forma confiable una variable seteada
rem con "set" al proceso siguiente cuando van juntos en una sola linea
rem "set X=1 && comando" (se confirmo a mano, repetible, el mismo dia -- ver
rem SES-164 en BITACORA.md). Como lineas separadas de un .bat, si funciona
rem siempre, igual que el patron que ya usa backend\_iniciar_backend.bat.
set MOTOSAFE_SIN_HTTPS=1

call npm run build
if errorlevel 1 (
    echo.
    echo Fallo "npm run build". Revisa el error de arriba.
    pause
    exit /b 1
)

call npx vite preview --host --port 5175 --strictPort
