@echo off
setlocal
pushd "%~dp0.."
set "ROOT=%CD%"
popd

echo ============================================
echo   MotoSafe GBA - Levantando app (Tailscale Funnel)
echo ============================================

where wt >nul 2>nul
if errorlevel 1 goto :sin_windows_terminal

echo.
echo Abriendo Docker, Backend, Frontend y Tailscale Funnel en pestanas de
echo la misma ventana (Windows Terminal)...
start "" wt -w 0 new-tab --title "MotoSafe - Docker" cmd /k "cd /d "%ROOT%" && docker compose up -d" ; new-tab --title "MotoSafe - Backend" cmd /k ""%ROOT%\backend\_iniciar_backend.bat"" ; new-tab --title "MotoSafe - Frontend" cmd /k ""%ROOT%\tailscale\_iniciar_frontend.bat"" ; new-tab --title "MotoSafe - Funnel" cmd /k ""%ROOT%\tailscale\iniciar_funnel.bat""

echo.
echo Listo. 4 pestanas: Docker, Backend, Frontend y Tailscale Funnel.
echo Backend:  http://localhost:8000 (no expuesto directo a internet)
echo Frontend: http://localhost:5175 (sin TLS propio a proposito -- Funnel ya pone HTTPS real de cara a internet; ver SES-164)
echo Publico:  revisa tailscale\public_url.txt despues de unos segundos
echo           (lo escribe la pestana "MotoSafe - Funnel").
echo.
echo Esta ventana se puede cerrar; la de Windows Terminal queda corriendo.
pause
exit /b

:sin_windows_terminal
echo.
echo Windows Terminal no esta instalado -- cada proceso en su propia ventana.

echo [1/4] Base de datos (Docker)...
cd /d "%ROOT%" && docker compose up -d
if errorlevel 1 (
    echo   ADVERTENCIA: fallo "docker compose up -d". ^¿Esta Docker Desktop abierto?
    pause
)

echo [2/4] Backend (FastAPI) en una terminal nueva...
start "MotoSafe - Backend" cmd /k ""%ROOT%\backend\_iniciar_backend.bat""

echo [3/4] Frontend (Vite) en otra terminal nueva...
start "MotoSafe - Frontend" cmd /k ""%ROOT%\tailscale\_iniciar_frontend.bat""

echo [4/4] Tailscale Funnel en otra terminal nueva...
start "MotoSafe - Funnel" cmd /k ""%ROOT%\tailscale\iniciar_funnel.bat""

echo.
echo Listo. Revisa tailscale\public_url.txt despues de unos segundos.
pause
