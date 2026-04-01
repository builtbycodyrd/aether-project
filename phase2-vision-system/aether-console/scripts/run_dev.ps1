$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$venvPy = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (!(Test-Path $venvPy)) {
    throw ".venv not found. Run .\scripts\install_deps.ps1 first."
}

& $venvPy (Join-Path $projectRoot "app\main.py")
