@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   MotoSafe GBA - Commitear cambios
echo ============================================
echo.

git status
echo.

set /p confirmar="Agregar TODOS los cambios de arriba y commitear? (s/n): "
if /i not "%confirmar%"=="s" (
    echo Cancelado.
    pause
    exit /b
)

git add -A

echo.
set /p mensaje="Mensaje del commit: "
if "%mensaje%"=="" (
    echo Mensaje vacio, cancelado.
    pause
    exit /b
)

git commit -m "%mensaje%"

echo.
set /p pushear="Pushear a origin ahora? (s/n): "
if /i "%pushear%"=="s" (
    git push
)

echo.
echo Listo.
pause
