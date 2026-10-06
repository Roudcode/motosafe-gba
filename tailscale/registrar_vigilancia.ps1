# Registra la tarea MotoSafe-Vigilancia (SES-085): corre vigilancia.ps1 al
# iniciar sesion y cada 5 minutos, sin ventana visible. Correr una sola vez:
#   powershell -ExecutionPolicy Bypass -File tailscale\registrar_vigilancia.ps1
# Si ya existe, la reemplaza. Solo ASCII (ver nota en vigilancia.ps1).
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'vigilancia.ps1'

$accion = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`"" `
    -WorkingDirectory (Split-Path -Parent $PSScriptRoot)

$alIniciarSesion = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$cadaCincoMinutos = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)

$config = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName 'MotoSafe-Vigilancia' -Action $accion `
    -Trigger @($alIniciarSesion, $cadaCincoMinutos) -Settings $config `
    -Description 'Vigila base, backend, preview 5175, Funnel y URL publica de MotoSafe; reinicia lo que falle (SES-085).' `
    -Force | Out-Null

$tarea = Get-ScheduledTask -TaskName 'MotoSafe-Vigilancia'
"estado=$($tarea.State)"
