param(
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1",
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = "E:/Miniconda/envs/NLP/python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "[restart_api] repoRoot=$repoRoot"
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

Set-Location $repoRoot

$args = @(
    "-m", "uvicorn",
    "api_server:app",
    "--host", $BindHost,
    "--port", $Port.ToString(),
    "--app-dir", $repoRoot
)

if ($Reload) {
    $args += "--reload"
}

Write-Host "[restart_api] starting: $pythonExe $($args -join ' ')"
& $pythonExe @args
