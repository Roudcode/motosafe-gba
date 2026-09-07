@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Levantando todo
echo ============================================

echo.
echo [1/2] Base de datos (Docker)...
docker compose up -d
if errorlevel 1 (
    echo   ADVERTENCIA: fallo "docker compose up -d". ^¿Esta Docker Desktop abierto?
    pause
)

where wt >nul 2>nul
if errorlevel 1 goto :sin_windows_terminal

echo.
echo [2/2] Abriendo Backend y Frontend en pestanas de la misma ventana (Windows Terminal)...
start "" wt -w 0 new-tab --title "MotoSafe - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload" ; new-tab --title "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Listo. Se abrio una ventana de Windows Terminal con 2 pestanas (Backend y Frontend).
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Esta ventana se puede cerrar; la de Windows Terminal queda corriendo la app.
pause
exit /b

:sin_windows_terminal
echo.
echo [2/2] Windows Terminal no esta instalado (comando "wt" no encontrado) --
echo       cada proceso se abre en su propia ventana de consola normal.
start "MotoSafe - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload"
start "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Listo. Se abrieron 2 terminales (Backend y Frontend).
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Tip: si instalas "Windows Terminal" desde la Microsoft Store, la proxima
echo vez este mismo script te las abre juntas en pestanas de una sola ventana.
echo.
echo Esta ventana se puede cerrar; las otras dos quedan corriendo la app.
pause
