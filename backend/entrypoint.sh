#!/bin/sh
set -eu

echo "[motosafe-api] aplicando migraciones versionadas"
python migrar.py

echo "[motosafe-api] iniciando API"
exec uvicorn main:app --host 0.0.0.0 --port 8000
