$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$venvDir = Join-Path $projectRoot ".venv"
$venvPy = Join-Path $venvDir "Scripts\python.exe"

Write-Host "=== Aether Console dependency installer ==="
Write-Host "Project root: $projectRoot"

if (!(Test-Path $venvPy)) {
    py -3.11 -m venv $venvDir
}

& $venvPy -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }

& $venvPy -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "requirements install failed" }

& $venvPy (Join-Path $projectRoot "scripts\download_models.py") yolov8n.pt
if ($LASTEXITCODE -ne 0) { throw "default YOLO model download failed" }

Write-Host "esptool and Python dependencies are ready." -ForegroundColor Green
Write-Host "Note: Pairing now expects bundled firmware assets under firmware_assets\." -ForegroundColor Yellow
Write-Host ""
Write-Host "Dependencies installed. Default YOLO model: yolov8n.pt" -ForegroundColor Green
