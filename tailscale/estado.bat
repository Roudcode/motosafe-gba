@echo off
setlocal

echo ============================================
echo   MotoSafe GBA - Estado
echo ============================================
echo.
echo === Tailscale (red) ===
tailscale status
echo.
echo === Tailscale Funnel ===
tailscale funnel status
echo.
echo === Backend local, puerto 8000 (esperado: 200) ===
curl -s -o nul -w "HTTP %%{http_code}\n" http://127.0.0.1:8000/health
echo.
echo === Frontend local, puerto 5173 HTTPS autofirmado (esperado: 200) ===
curl -sk -o nul -w "HTTP %%{http_code}\n" https://127.0.0.1:5173/
echo.
if exist "%~dp0public_url.txt" (
    set /p URL=<"%~dp0public_url.txt"
    echo === URL publica ^(%URL%^), esperado: 200 desde CUALQUIER red ===
    curl -s -o nul -w "HTTP %%{http_code}\n" "%URL%/"
) else (
    echo No encontre tailscale\public_url.txt todavia -- corre
    echo iniciar_funnel.bat primero.
)
echo.
pause
