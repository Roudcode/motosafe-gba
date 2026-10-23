# Vigilancia del acceso publico de MotoSafe (SES-085).
# Revisa, en orden: base (Postgres en Docker), backend (8000), preview del
# frontend (5175), Tailscale Funnel (443 -> 5175) y la URL publica. Si algo
# falla, lo reinicia y lo deja registrado en logs\vigilancia.
#
#   powershell -File tailscale\vigilancia.ps1               revisa y reinicia lo que falle
#   powershell -File tailscale\vigilancia.ps1 -SoloEstado   solo muestra el estado, sin tocar nada
#
# Lo ejecuta la tarea programada MotoSafe-Vigilancia (ver registrar_vigilancia.ps1).
# Solo ASCII a proposito: Windows PowerShell 5.1 lee mal UTF-8 sin BOM.
param([switch]$SoloEstado)

$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$puerto = 5175
$dockerExe = 'C:\Users\rodol\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe'
$dirLog = Join-Path $raiz 'logs\vigilancia'
New-Item -ItemType Directory -Force -Path $dirLog | Out-Null
$log = Join-Path $dirLog ('vigilancia_{0}.log' -f (Get-Date -Format 'yyyyMMdd'))

$urlPublica = (Get-Content (Join-Path $PSScriptRoot 'public_url.txt') -ErrorAction SilentlyContinue | Select-Object -First 1)
if ($urlPublica) { $urlPublica = $urlPublica.Trim() }

# curl.exe (incluido en Windows 10/11) en vez de Invoke-WebRequest: el preview
# local usa HTTPS con certificado autofirmado, y -k lo acepta sin tocar
# callbacks de PowerShell 5.1 (que fallan en hilos de trabajo).
function Get-CodigoHttp([string]$url) {
    $codigo = & curl.exe -sk -o NUL -w '%{http_code}' --max-time 15 $url 2>$null
    if ($codigo -match '^\d+$') { return [int]$codigo }
    return 0
}

function Test-Base { docker exec motosafe-db pg_isready -U motosafe -d motosafe_gba *> $null; return ($LASTEXITCODE -eq 0) }
function Test-Backend { return ((Get-CodigoHttp 'http://127.0.0.1:8000/health') -eq 200) }
function Test-Preview { return ((Get-CodigoHttp "http://127.0.0.1:$puerto/") -eq 200) }
function Test-Funnel {
    $estado = (tailscale funnel status 2>&1 | Out-String)
    return ($estado -match 'Funnel on' -and $estado -match "proxy http://127\.0\.0\.1:$puerto")
}
function Test-Publica { if (-not $urlPublica) { return $false }; return ((Get-CodigoHttp $urlPublica) -eq 200) }

function Escribir([string]$texto) {
    $linea = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $texto
    Add-Content -Path $log -Value $linea -Encoding UTF8
    if ($SoloEstado) { Write-Host $texto }
}

function Esperar([scriptblock]$condicion, [int]$segundos) {
    $limite = (Get-Date).AddSeconds($segundos)
    while ((Get-Date) -lt $limite) {
        if (& $condicion) { return $true }
        Start-Sleep -Seconds 3
    }
    return $false
}

$acciones = @()

# 1. Base de datos: Docker Desktop y el contenedor motosafe-db.
if (-not (Test-Base) -and -not $SoloEstado) {
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Start-Process -FilePath $dockerExe
        Esperar { docker info *> $null; $LASTEXITCODE -eq 0 } 300 | Out-Null
    }
    docker start motosafe-db *> $null
    $acciones += 'base: docker start'
    # Postgres tarda unos segundos en aceptar conexiones tras el start.
    Esperar { Test-Base } 60 | Out-Null
}
$baseOk = Test-Base

# 2. Backend nativo (run_dev.py con _iniciar_backend.bat).
$backendOk = Test-Backend
if (-not $backendOk -and -not $SoloEstado -and $baseOk) {
    # uvicorn --reload deja un proceso hijo (multiprocessing) que puede seguir con
    # el socket abierto aunque su padre haya muerto. Se limpian esos restos antes
    # de levantar uno nuevo, para no chocar con el puerto 8000.
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'run_dev\.py|multiprocessing\.spawn' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "`"$raiz\backend\_iniciar_backend.bat`"" -WindowStyle Hidden
    $acciones += 'backend: iniciado'
    $backendOk = Esperar { Test-Backend } 120
}

# 3. Preview del frontend (build de produccion servido por vite preview).
$previewOk = Test-Preview
if (-not $previewOk -and -not $SoloEstado) {
    Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    $frontend = Join-Path $raiz 'frontend'
    if (-not (Test-Path (Join-Path $frontend 'dist\index.html'))) {
        Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "cd /d `"$frontend`" && npm run build" -WindowStyle Hidden -Wait
        $acciones += 'preview: build'
    }
    # MOTOSAFE_SIN_HTTPS seteado en el entorno de ESTE proceso (no dentro de
    # la linea de cmd.exe): un "set X=1 && comando" en una sola linea de
    # cmd.exe no propaga de forma confiable la variable al comando siguiente
    # (confirmado a mano, repetible -- ver SES-164 en BITACORA.md). Start-Process
    # hereda el entorno de este proceso de PowerShell, asi que seteandola aca
    # alcanza, sin tocar la linea de cmd.exe.
    $env:MOTOSAFE_SIN_HTTPS = '1'
    Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "cd /d `"$frontend`" && npx vite preview --host --port $puerto --strictPort" -WindowStyle Hidden
    $acciones += 'preview: iniciado'
    $previewOk = Esperar { Test-Preview } 60
}

# 4. Tailscale Funnel: el 443 tiene que apuntar al preview. El 8443 no se toca.
$funnelOk = Test-Funnel
if (-not $funnelOk -and -not $SoloEstado) {
    tailscale funnel --bg --https=443 "http://127.0.0.1:$puerto" *> $null
    $acciones += 'funnel: reaplicado a 443'
    $funnelOk = Test-Funnel
}

# 5. URL publica: responde 200 desde afuera (Funnel + preview + certificado de Tailscale).
$publicaOk = Test-Publica
if (-not $publicaOk -and -not $SoloEstado -and $funnelOk -and $previewOk) {
    Start-Sleep -Seconds 10
    $publicaOk = Test-Publica
    if (-not $publicaOk) { $acciones += 'publica: no responde tras reaplicar' }
}

function Marca([bool]$ok) { if ($ok) { 'OK' } else { 'FALLA' } }
$publicaTexto = if ($urlPublica) { "$(Marca $publicaOk) ($urlPublica)" } else { 'SIN URL (falta public_url.txt)' }
$resumen = "base={0} backend={1} preview={2} funnel={3} publica={4}" -f (Marca $baseOk), (Marca $backendOk), (Marca $previewOk), (Marca $funnelOk), (Marca $publicaOk)
$detalle = if ($acciones.Count) { $acciones -join '; ' } else { 'sin acciones' }

if ($SoloEstado) {
    Write-Host ''
    Write-Host ('  Base (Postgres)    : ' + (Marca $baseOk))
    Write-Host ('  Backend  :8000     : ' + (Marca $backendOk))
    Write-Host ('  Preview  :5175     : ' + (Marca $previewOk))
    Write-Host ('  Funnel 443 -> 5175 : ' + (Marca $funnelOk))
    Write-Host ('  URL publica        : ' + $publicaTexto)
    Write-Host ''
} else {
    Escribir ("{0} | {1}" -f $resumen, $detalle)
}
