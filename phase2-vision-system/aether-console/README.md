# AetherConsole

A professional desktop application for pairing, provisioning, previewing, and tuning ESP32-CAM devices with built-in YOLOv8 object detection support.

## Quick Start

```powershell
# Install dependencies
.\scripts\install_deps.ps1

# Run the application
.\scripts\run_dev.ps1
```

## What is AetherConsole?

AetherConsole is a development tool for the Aether Project's vision system (Phase 2). It provides:
- USB serial ESP32-CAM pairing and firmware flashing
- Wi-Fi provisioning
- Live MJPEG stream preview
- Comprehensive camera tuning controls
- YOLOv8 object detection with multiple model options
- Multi-board support

This app is used to **configure and test** the ESP32-CAM before deploying it as part of the larger Aether robotic system.

## Features

- ✅ **Built-in ESP32-CAM flasher** (no Arduino IDE needed)
- ✅ **Live camera preview** over Wi-Fi
- ✅ **Full camera control** (resolution, quality, exposure, white balance, etc.)
- ✅ **YOLOv8 object detection** with 5 model sizes
- ✅ **Multi-board support** (AI Thinker, ESP-EYE, M5Stack, etc.)
- ✅ **Modern PyQt6 interface**
- ✅ **On-demand model downloads**
- ✅ **Persistent configuration**

## Requirements

- Python 3.10 or higher
- Windows (current platform)
- ESP32-CAM device
- USB to serial adapter (if needed)

## Installation

### Option 1: Automated (Recommended)
```powershell
.\scripts\install_deps.ps1
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Download the default YOLOv8n model

### Option 2: Manual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running the App

```powershell
.\scripts\run_dev.ps1
```

Or manually:
```powershell
.\.venv\Scripts\Activate.ps1
python -m app.main
```

## Usage Guide

### 1. Pair Your ESP32-CAM (First Time)

1. Connect ESP32-CAM to your computer via USB
2. Open AetherConsole
3. Go to the **Setup** tab
4. Click **"Scan Ports"** to detect your board
5. Review the recommended board type (or select manually)
6. Enter your **Wi-Fi SSID** and **password**
7. Click **"Pair Camera"** to flash firmware

**Note:** The firmware flashing feature requires firmware assets to be built. See "Known Issues" section.

### 2. Preview Camera Stream

1. Go to the **Preview** tab
2. Camera stream should appear automatically (after successful pairing)
3. Use the **Camera** tab to adjust settings in real-time

### 3. Enable Object Detection

1. Go to the **Detection** tab
2. Select a YOLO model (yolov8n is default)
3. Download larger models if needed:
   - `yolov8s` - Small (faster, less accurate)
   - `yolov8m` - Medium (balanced)
   - `yolov8l` - Large (slower, more accurate)
   - `yolov8x` - Extra Large (slowest, most accurate)
4. Adjust confidence threshold (default: 0.25)
5. Enable specific object classes
6. Check "Enable Detection" to see overlay on preview

### 4. Tune Camera Settings

Use the **Camera** tab to adjust:
- **Resolution:** VGA, SVGA, XGA, HD, FHD, etc.
- **Quality:** JPEG compression (0-63, lower = better)
- **Exposure:** AEC, AE level, AGC controls
- **White Balance:** AWB modes, manual WB
- **Image Adjustments:** Brightness, contrast, saturation, sharpness
- **Advanced:** Lens correction, black pixel correction, gamma

Click **"Apply Settings"** to update the camera.

## Project Structure

```
aether-console/
├── app/                    # Application source code
│   ├── main.py            # Main window and UI
│   ├── camera_api.py      # ESP32 HTTP API interface
│   ├── detection.py       # YOLO detection integration
│   ├── stream_worker.py   # Background stream worker
│   ├── model_manager.py   # Model download & management
│   ├── config_manager.py  # Configuration persistence
│   ├── pairing.py         # ESP32-CAM pairing workflow
│   └── board_profiles.py  # Board metadata
├── config/                # Configuration files
├── firmware_src/          # ESP32-CAM firmware source
├── firmware_assets/       # Compiled firmware binaries
├── installer/             # Windows installer scripts
├── scripts/               # Build and utility scripts
└── requirements.txt       # Python dependencies
```

## Configuration

User configuration is stored at:
```
%LOCALAPPDATA%\AetherConsole\config.json
```

Downloaded YOLO models are stored at:
```
%LOCALAPPDATA%\AetherConsole\models\
```

## Known Issues

1. **Firmware flashing incomplete** - Firmware assets need to be compiled by maintainer before pairing works. Build script available at `scripts/build_firmware_assets.ps1`.

2. **No packaged installer yet** - App currently runs from source. Packaging scripts are ready but need final build.

3. **Camera setting timeouts** - Rapid setting changes may timeout. Solution: pace requests.

## Supported Boards

### Fully Supported
- ✅ AI Thinker ESP32-CAM

### In Progress
- ⏳ ESP-EYE
- ⏳ M5Stack UnitCam
- ⏳ Seeed XIAO ESP32S3 Sense
- ⏳ ESP32 Wrover Kit
- ⏳ M5Stack ESP32CAM
- ⏳ TTGO T-Journal
- ⏳ FireBeetle 2 ESP32-S3

## Development

### Building Firmware Assets

For maintainers with Arduino CLI installed:

```powershell
.\scripts\build_firmware_assets.ps1 -Board ai_thinker
```

This generates:
- `firmware_assets/ai_thinker/bootloader.bin`
- `firmware_assets/ai_thinker/partitions.bin`
- `firmware_assets/ai_thinker/firmware.bin`

### Building Windows Installer

```powershell
.\scripts\build_windows.ps1
```

Uses PyInstaller + Inno Setup to create distributable installer.

## Technical Details

### Dependencies
- **PyQt6** - GUI framework
- **OpenCV** - Video streaming
- **Ultralytics** - YOLOv8 implementation
- **PyTorch** - Deep learning backend
- **esptool** - ESP32 firmware flashing
- **pyserial** - Serial communication

### ESP32-CAM Communication
- **Pairing:** USB serial at 115200 baud
- **Runtime:** Wi-Fi HTTP
  - Stream: `http://<camera-ip>:81/stream` (MJPEG)
  - Control: `http://<camera-ip>/control?var=<param>&val=<value>`
  - Status: `http://<camera-ip>/status`

## Troubleshooting

### Camera not detected
- Ensure ESP32-CAM is connected via USB
- Check that USB-to-serial drivers are installed
- Try clicking "Scan Ports" again

### Stream not loading
- Verify camera is powered on
- Check Wi-Fi connection
- Confirm camera IP is reachable
- Try direct IP instead of mDNS (`aether-camera.local`)

### Detection is slow
- Use a smaller model (yolov8n or yolov8s)
- Reduce inference image size
- Check that GPU is being used (if available)
- Lower stream resolution

### YOLO model download fails
- Check internet connection
- Models are large (50MB - 200MB+)
- Retry download - corrupt downloads are automatically cleaned up

## Part of the Aether Project

This application is **Phase 2** of the larger Aether Project - an AI-powered robotic desktop companion.

- **Phase 1:** Robotic arm (physical manipulation)
- **Phase 2:** Vision system (**this app** - computer vision)
- **Phase 3:** AI assistant (intelligence and coordination)

AetherConsole is used to develop and tune the vision system before integrating it with the robotic arm and AI assistant.

## License

Part of the Aether Project by builtbycodyrd.

Based on ESP32 CameraWebServer examples from Espressif Systems.
YOLOv8 by Ultralytics.

---

For full project documentation, see: [Phase 2 README](../README.md)
