# Aether CameraWebServer Firmware Workspace

This folder is the first real firmware-source workspace for `Aether Console`.

## Intent

This is the maintainer-side source tree that should eventually produce the bundled firmware assets shipped under `firmware_assets/`.

It is based on the operating contract established by Espressif's CameraWebServer example:
- initialize the ESP32 camera correctly for the selected board
- join Wi-Fi as a station
- expose MJPEG preview
- expose a stable HTTP control API for camera tuning

The Aether-specific changes are intended to standardize the endpoints that the desktop app expects:
- `GET /stream` on port `81`
- `GET /status` on port `80`
- `GET /control?var=...&val=...` on port `80`

## Current scope

Current concrete target:
- `AI Thinker ESP32-CAM`

Other boards remain planned, but they should not be treated as validated until they compile and pass hardware testing.

## Current limitations

- This source workspace has not yet been compiled or hardware-validated in this environment.
- The current build config still uses compile-time Wi-Fi defaults in `aether_build_config.h`.
- The long-term pairing design still needs a cleaner per-device provisioning path so the app can inject credentials without baking user secrets into release binaries.
- The app-side flasher is ready for packaged binaries, but those binaries do not exist yet.

## Files

- `AetherCameraWebServer.ino`: initial firmware sketch aligned with the desktop app's preview and `/control` expectations.
- `camera_pins_aether.h`: validated starting pin map for the first board target.
- `aether_build_config.h`: build-time defaults and placeholders.

## Build direction

Use the maintainer build script at `scripts/build_firmware_assets.ps1` to compile this source into the packaged `firmware_assets/ai_thinker/` layout once the Arduino build toolchain is available.

This script is for maintainers and release engineering only. End users should never need Arduino CLI installed just to pair a camera.
