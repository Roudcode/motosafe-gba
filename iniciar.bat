@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Levantando todo
echo ============================================

where wt >nul 2>nul
if errorlevel 1 goto :sin_windows_terminal

echo.
echo Abriendo Docker, Backend, Frontend y Tunel en pestanas de la misma ventana (Windows Terminal)...
start "" wt -w 0 new-tab --title "MotoSafe - Docker" cmd /k "cd /d %~dp0 && docker compose up -d" ; new-tab --title "MotoSafe - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload" ; new-tab --title "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev" ; new-tab --title "MotoSafe - Tunel" cmd /k "cloudflared tunnel --url https://localhost:5173 --no-tls-verify"

echo.
echo Listo. Se abrio una ventana de Windows Terminal con 4 pestanas (Docker, Backend, Frontend y Tunel).
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Tunel:    fijate el link *.trycloudflare.com en la pestana "MotoSafe - Tunel"
echo           (cambia cada vez que se levanta, no es siempre el mismo).
echo           Lleva --no-tls-verify porque Vite sirve HTTPS con certificado
echo           autofirmado, y sin ese flag cloudflared no confia en el
echo           certificado y tira 502 Bad Gateway.
echo.
echo Esta ventana se puede cerrar; la de Windows Terminal queda corriendo la app.
pause
exit /b

:sin_windows_terminal
echo.
echo Windows Terminal no esta instalado (comando "wt" no encontrado) --
echo cada proceso se abre en su propia ventana de consola normal.

echo [1/4] Base de datos (Docker)...
docker compose up -d
if errorlevel 1 (
    echo   ADVERTENCIA: fallo "docker compose up -d". ^¿Esta Docker Desktop abierto?
    pause
)

echo [2/4] Backend (FastAPI) en una terminal nueva...
start "MotoSafe - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload"

echo [3/4] Frontend (Vite) en otra terminal nueva...
start "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo [4/4] Tunel (Cloudflare) en otra terminal nueva...
start "MotoSafe - Tunel" cmd /k "cloudflared tunnel --url https://localhost:5173 --no-tls-verify"

echo.
echo Listo. Se abrieron 3 terminales (Backend, Frontend y Tunel), Docker corrio en esta misma ventana.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo Tunel:    fijate el link *.trycloudflare.com en la terminal "MotoSafe - Tunel"
echo           (cambia cada vez que se levanta, no es siempre el mismo).
echo           Lleva --no-tls-verify porque Vite sirve HTTPS con certificado
echo           autofirmado, y sin ese flag cloudflared no confia en el
echo           certificado y tira 502 Bad Gateway.
echo.
echo Tip: si instalas "Windows Terminal" desde la Microsoft Store, la proxima
echo vez este mismo script te abre las 4 pestanas juntas en una sola ventana.
echo.
echo Esta ventana se puede cerrar; las otras tres quedan corriendo la app.
pause
