@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Levantando todo
echo ============================================

where wt >nul 2>nul
if errorlevel 1 goto :sin_windows_terminal

echo.
echo Abriendo Docker, Backend, Frontend, Scraper y Tunel en pestanas de la misma ventana (Windows Terminal)...
start "" wt -w 0 new-tab --title "MotoSafe - Docker" cmd /k "cd /d %~dp0 && docker compose up -d" ; new-tab --title "MotoSafe - Backend" cmd /k "%~dp0backend\_iniciar_backend.bat" ; new-tab --title "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev" ; new-tab --title "MotoSafe - Scraper" cmd /k "cd /d %~dp0backend && venv312\Scripts\activate && python scrapear_noticias_robos.py --guardar" ; new-tab --title "MotoSafe - Tunel" cmd /k "cloudflared tunnel --url https://localhost:5173 --no-tls-verify"

echo.
echo Listo. Se abrio una ventana de Windows Terminal con 5 pestanas (Docker, Backend, Frontend, Scraper y Tunel).
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
start "MotoSafe - Backend" cmd /k "%~dp0backend\_iniciar_backend.bat"

echo [3/4] Frontend (Vite) en otra terminal nueva...
start "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo [4/5] Scraper de noticias en otra terminal nueva...
start "MotoSafe - Scraper" cmd /k "cd /d %~dp0backend && venv312\Scripts\activate && python scrapear_noticias_robos.py --guardar"

echo [5/5] Tunel (Cloudflare) en otra terminal nueva...
start "MotoSafe - Tunel" cmd /k "cloudflared tunnel --url https://localhost:5173 --no-tls-verify"

echo.
echo Listo. Se abrieron 4 terminales (Backend, Frontend, Scraper y Tunel), Docker corrio en esta misma ventana.
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
