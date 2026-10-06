@echo off
setlocal
cd /d "%~dp0"
call venv312\Scripts\activate

echo Verificando dependencias de Python (rapido si ya estan instaladas)...
pip install -q --require-hashes -r requirements.lock

python -c "import os,sys; from dotenv import load_dotenv; load_dotenv(); sys.exit(0 if (os.getenv('AUTH_USERNAME') and os.getenv('AUTH_PASSWORD_HASH')) else 1)"
if errorlevel 1 (
    echo.
    echo Todavia no configuraste el usuario/contrasena de acceso a la app.
    echo Generandolo ahora...
    echo.
    python generar_password.py
    echo.
    echo Pega las dos lineas de arriba ^(AUTH_USERNAME y AUTH_PASSWORD_HASH^)
    echo en backend\.env, guarda el archivo y volve a correr este script.
    pause
    exit /b 1
)

python run_dev.py
