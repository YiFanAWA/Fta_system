param(
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1",
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

$appDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $appDir
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path -LiteralPath $venvPython) {
    $venvPython
}
else {
    "python"
}

Write-Host "[restart_api] appDir=$appDir"
Write-Host "[restart_api] python=$pythonExe"
Write-Host "[restart_api] target=$BindHost`:$Port"

$procIds = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

if ($procIds) {
    foreach ($procId in $procIds) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "[restart_api] killed PID=$procId on port $Port"
        }
        catch {
            Write-Warning "[restart_api] failed to kill PID=$procId : $($_.Exception.Message)"
        }
    }
}
else {
    Write-Host "[restart_api] no listener on port $Port"
}

Set-Location $projectRoot

$uvicornArgs = @(
    "-m", "uvicorn",
    "app.api_server:app",
    "--host", $BindHost,
    "--port", $Port.ToString(),
    "--app-dir", $appDir
)

if ($Reload) {
    $uvicornArgs += "--reload"
}

Write-Host "[restart_api] starting: $pythonExe $($uvicornArgs -join ' ')"
& $pythonExe @uvicornArgs
