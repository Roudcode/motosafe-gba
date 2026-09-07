@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Levantando todo
echo ============================================

where wt >nul 2>nul
if errorlevel 1 goto :sin_windows_terminal

echo.
echo Abriendo Docker, Backend y Frontend en pestanas de la misma ventana (Windows Terminal)...
start "" wt -w 0 new-tab --title "MotoSafe - Docker" cmd /k "cd /d %~dp0 && docker compose up -d" ; new-tab --title "MotoSafe - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload" ; new-tab --title "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Listo. Se abrio una ventana de Windows Terminal con 3 pestanas (Docker, Backend y Frontend).
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Esta ventana se puede cerrar; la de Windows Terminal queda corriendo la app.
pause
exit /b

:sin_windows_terminal
echo.
echo Windows Terminal no esta instalado (comando "wt" no encontrado) --
echo cada proceso se abre en su propia ventana de consola normal.

echo [1/3] Base de datos (Docker)...
docker compose up -d
if errorlevel 1 (
    echo   ADVERTENCIA: fallo "docker compose up -d". ^¿Esta Docker Desktop abierto?
    pause
)

echo [2/3] Backend (FastAPI) en una terminal nueva...
start "MotoSafe - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload"

echo [3/3] Frontend (Vite) en otra terminal nueva...
start "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Listo. Se abrieron 2 terminales (Backend y Frontend), Docker corrio en esta misma ventana.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Tip: si instalas "Windows Terminal" desde la Microsoft Store, la proxima
echo vez este mismo script te abre las 3 pestanas juntas en una sola ventana.
echo.
echo Esta ventana se puede cerrar; las otras dos quedan corriendo la app.
pause
