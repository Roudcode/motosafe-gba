@echo off
rem Corrida programada del scraper de prensa contra la base de produccion (SES-081).
rem   scraper_programado.bat          guarda en la base (corrida real)
rem   scraper_programado.bat --seco   prueba sin guardar nada
rem Cada corrida deja su log en logs\scraper\corrida_AAAAMMDD_HHMMSS.log
setlocal
cd /d "%~dp0"

rem Compose da prioridad a las variables de entorno de Windows sobre --env-file,
rem asi que una DATABASE_URL del usuario pisaria .env.production. Se vacian solo
rem para este proceso; no se toca el entorno del usuario.
set "DATABASE_URL="
set "CORS_ALLOWED_ORIGINS="
set "TOMTOM_API_KEY="
set "POSTGRES_USER="
set "POSTGRES_PASSWORD="
set "POSTGRES_DB="
set "SCRAPER_INTERVAL_MINUTES="
set "SCRAPER_TIMEOUT_MINUTES="

if not exist ".env.production" (
    echo No existe .env.production en %CD%. Abortando.
    exit /b 1
)

set "LOG_DIR=%~dp0logs\scraper"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
for /f %%F in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "MARCA=%%F"
set "LOG=%LOG_DIR%\corrida_%MARCA%.log"

set "MODO=--guardar"
if /i "%~1"=="--seco" set "MODO="

rem Limpieza: borra solo corrida_*.log de mas de 60 dias en logs\scraper, antes de correr.
forfiles /P "%LOG_DIR%" /M corrida_*.log /D -60 /C "cmd /c echo [%date% %time%] limpieza: borrando @file & del /q @path" >> "%LOG%" 2>nul

echo [%date% %time%] inicio (modo: %MODO%) >> "%LOG%"

rem Docker Desktop arranca con el inicio de sesion pero tarda: esperamos hasta 5 minutos.
set /a INTENTOS=0
:esperar_docker
docker info >nul 2>&1
if not errorlevel 1 goto :ejecutar
set /a INTENTOS+=1
if %INTENTOS% GEQ 30 (
    echo [%date% %time%] Docker no responde tras 5 minutos. Abortando. >> "%LOG%"
    exit /b 2
)
ping -n 11 127.0.0.1 >nul
goto :esperar_docker

:ejecutar
docker compose --env-file .env.production -f docker-compose.production.yml run --rm --build --quiet-build --no-deps --entrypoint python scraper scrapear_noticias_robos.py %MODO% >> "%LOG%" 2>&1
set "CODIGO=%ERRORLEVEL%"
echo [%date% %time%] fin codigo=%CODIGO% >> "%LOG%"
exit /b %CODIGO%
