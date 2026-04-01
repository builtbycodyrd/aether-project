param(
    [string]$Board = "ai_thinker",
    [string]$WifiSsid = "CHANGE_ME_WIFI",
    [string]$WifiPassword = "CHANGE_ME_PASSWORD",
    [string]$Hostname = "aether-camera",
    [string]$CameraName = "Aether Camera"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$sourceDir = Join-Path $projectRoot "firmware_src\aether_camerawebserver"
$buildRoot = Join-Path $projectRoot ".firmware_build"
$outDir = Join-Path $projectRoot "firmware_assets\$Board"

$boardMap = @{
    "ai_thinker" = @{ fqbn = "esp32:esp32:esp32cam"; sketch = $sourceDir }
}

if (-not $boardMap.ContainsKey($Board)) {
    throw "Unsupported board '$Board' for the current maintainer build script. Start with ai_thinker."
}

$arduinoCli = Get-Command arduino-cli -ErrorAction SilentlyContinue
if (-not $arduinoCli) {
    throw "arduino-cli is required for maintainer firmware builds. Install it on the build machine, not the end-user machine."
}

$boardInfo = $boardMap[$Board]
$fqbn = $boardInfo.fqbn
$buildDir = Join-Path $buildRoot $Board
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$extraFlags = @(
    "-DAETHER_WIFI_SSID=\"$WifiSsid\"",
    "-DAETHER_WIFI_PASSWORD=\"$WifiPassword\"",
    "-DAETHER_HOSTNAME=\"$Hostname\"",
    "-DAETHER_CAMERA_NAME=\"$CameraName\""
) -join " "

Write-Host "Compiling firmware for $Board ($fqbn)" -ForegroundColor Cyan
& $arduinoCli.Source compile --fqbn $fqbn --build-path $buildDir --build-property "build.extra_flags=$extraFlags" --export-binaries $sourceDir
if ($LASTEXITCODE -ne 0) {
    throw "Firmware compile failed."
}

$baseName = "AetherCameraWebServer.ino"
$bootloader = Join-Path $buildDir "$baseName.bootloader.bin"
$partitions = Join-Path $buildDir "$baseName.partitions.bin"
$firmware = Join-Path $buildDir "$baseName.bin"

if (!(Test-Path $bootloader) -or !(Test-Path $partitions) -or !(Test-Path $firmware)) {
    throw "Expected output binaries were not produced. Check the build directory and board profile."
}

Copy-Item $bootloader (Join-Path $outDir "bootloader.bin") -Force
Copy-Item $partitions (Join-Path $outDir "partitions.bin") -Force
Copy-Item $firmware (Join-Path $outDir "firmware.bin") -Force

Write-Host "Firmware assets written to $outDir" -ForegroundColor Green
Write-Host "These binaries are for packaging/testing only and still require hardware validation." -ForegroundColor Yellow
