$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$venvPy = Join-Path $projectRoot ".venv\Scripts\python.exe"
$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$installerOut = Join-Path $projectRoot "dist_installer"
$mainPy = Join-Path $projectRoot "app\main.py"
$defaultConfig = Join-Path $projectRoot "config\default_config.json"
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"

if (!(Test-Path $venvPy)) {
    throw ".venv not found. Run .\scripts\install_deps.ps1 first."
}

Remove-Item $distDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $installerOut -Recurse -Force -ErrorAction SilentlyContinue

& $venvPy -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "AetherConsole" `
  --add-data "$defaultConfig;config" `
  $mainPy

New-Item -ItemType Directory -Force -Path $installerOut | Out-Null

if (Test-Path $iscc) {
    & $iscc "/DMyAppRoot=$projectRoot" (Join-Path $projectRoot "installer\aether_console.iss")
    Write-Host "Installer created in $installerOut" -ForegroundColor Green
} else {
    Write-Host "Inno Setup 6 was not found. Packaged app is available in dist\AetherConsole." -ForegroundColor Yellow
}
