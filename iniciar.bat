@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Levantando todo
echo ============================================

echo.
echo [1/3] Base de datos (Docker)...
docker compose up -d
if errorlevel 1 (
    echo   ADVERTENCIA: fallo "docker compose up -d". ^¿Esta Docker Desktop abierto?
    pause
)

echo.
echo [2/3] Backend (FastAPI) en una terminal nueva...
start "MotoSafe - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn main:app --reload"

echo.
echo [3/3] Frontend (Vite) en otra terminal nueva...
start "MotoSafe - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Listo. Se abrieron 2 terminales (Backend y Frontend).
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Esta ventana se puede cerrar; las otras dos quedan corriendo la app.
pause
