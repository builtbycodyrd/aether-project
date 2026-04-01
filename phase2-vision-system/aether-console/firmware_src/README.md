# Firmware Source

This folder now contains the first real `Aether Console` firmware-source workspace under `aether_camerawebserver/`.

Base reference direction:
- Official Espressif camera stack: `espressif/esp32-camera`
- Official Arduino camera web-server example family: `espressif/arduino-esp32` CameraWebServer example

Current implemented workspace:
- `firmware_src/aether_camerawebserver/aether_camerawebserver.ino`
- `firmware_src/aether_camerawebserver/camera_pins_aether.h`
- `firmware_src/aether_camerawebserver/aether_build_config.h`
- `firmware_src/aether_camerawebserver/README.md`

Current state:
- The app-side flasher architecture is already pivoted to the professional bundled-firmware model.
- The first concrete firmware source workspace now exists for `AI Thinker ESP32-CAM`.
- A maintainer build script now exists at `scripts/build_firmware_assets.ps1` to generate `bootloader.bin`, `partitions.bin`, and `firmware.bin` into `firmware_assets/ai_thinker/`.
- Portable `arduino-cli` was extracted locally into `tools/arduino-cli/` and the ESP32 Arduino core was installed locally.
- The user's attached serial adapter is visible on `COM7`.
- A real compile was attempted and reached the bootloader-generation step.
- The current build blocker is the ESP32 platform's bundled `esptool.exe`, which fails on this Windows environment while extracting `VCRUNTIME140.dll`.
- The next concrete workaround is to repair the local Python `esptool` package and use it to bypass that broken packaged executable.

First real firmware milestone:
Concrete source target now added:
- `AI Thinker ESP32-CAM`

Intended next validated targets after AI Thinker:
- `ESP-EYE`
- `M5Stack UnitCam`
- `Seeed XIAO ESP32S3 Sense`

Visible in app but still in progress:
- `ESP32 Wrover Kit`
- `M5Stack ESP32CAM`
- `TTGO T-Journal`
- `FireBeetle 2 ESP32-S3`

Recommended next firmware steps:
1. Repair or reinstall the venv Python `esptool` package.
2. Use that to bypass the failing bundled `esptool.exe` step.
3. Retry the AI Thinker compile.
4. Confirm generation of `bootloader.bin`, `partitions.bin`, and `firmware.bin`.
5. Flash the resulting package to `COM7` and test runtime behavior.

Future-session rule:
- If the supported board set, firmware source layout, or packaging strategy changes, update this file, `CONTEXT.md`, and `PROJECT_STATE.md` before the session ends.
