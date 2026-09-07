@echo off
setlocal
cd /d "%~dp0backend"
call venv\Scripts\activate

:menu
cls
echo ============================================
echo   MotoSafe GBA - Tareas
echo ============================================
echo   1. Correr tests (pytest)
echo   2. Cargar hotspots en la base
echo   3. Cargar corredores en la base
echo   4. Descargar clima historico (una vez)
echo   5. Descargar geometria de corredores (OSRM)
echo   6. Descargar delitos CABA (una vez)
echo   7. Identificar corredores (sin red, agrupa siniestros por calle)
echo   8. Lint + build del frontend
echo   0. Salir
echo ============================================
set /p opcion="Elegi una opcion: "

if "%opcion%"=="1" (
    pytest
    pause
    goto menu
)
if "%opcion%"=="2" (
    python cargar_hotspots.py
    pause
    goto menu
)
if "%opcion%"=="3" (
    python cargar_corredores.py
    pause
    goto menu
)
if "%opcion%"=="4" (
    python ..\notebooks\fetch_clima_historico.py
    pause
    goto menu
)
if "%opcion%"=="5" (
    python ..\notebooks\fetch_corredores_geometria.py
    pause
    goto menu
)
if "%opcion%"=="6" (
    python ..\notebooks\fetch_delitos_caba.py
    pause
    goto menu
)
if "%opcion%"=="7" (
    pushd ..
    python notebooks\identificar_corredores.py
    popd
    pause
    goto menu
)
if "%opcion%"=="8" (
    pushd ..\frontend
    call npm run lint
    call npm run build
    popd
    pause
    goto menu
)
if "%opcion%"=="0" (
    exit
)
goto menu
