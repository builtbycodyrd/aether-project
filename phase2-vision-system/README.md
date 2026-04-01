# Phase 2: Computer Vision System

**Status:** ✅ Development Tool Complete

ESP32-CAM vision system with YOLOv8 object detection - the "eyes" of the Aether Project.

## Evolution

**Version 1 (Original):** Abandoned - unreliable, monolithic architecture  
**Version 2 (AlphaV1):** Deprecated - functional but limited features  
**Version 3 (AetherConsole):** ✅ Current - professional, feature-complete

## AetherConsole - Current Version

A professional desktop application for ESP32-CAM pairing, provisioning, and tuning.

### Features
- Built-in ESP32-CAM flasher (no Arduino IDE needed)
- Live MJPEG stream preview over Wi-Fi
- Comprehensive camera tuning (resolution, exposure, white balance, etc.)
- YOLOv8 object detection with 5 model sizes
- Multi-board support (AI Thinker, ESP-EYE, M5Stack, etc.)
- Modern PyQt6 interface

### Architecture
- 8 modular Python files (1,515 lines total)
- main.py, pairing.py, detection.py, camera_api.py, etc.
- Clean separation of concerns

### Status
✅ Working - Desktop app complete and functional  
⚠️ Known issues - Firmware assets need maintainer build, no installer yet  
⏳ Next step - Physical integration with robotic arm

## Purpose

AetherConsole is a **development tool** to tune the vision system before deploying it. Once configured, the ESP32-CAM will be mounted to the robotic arm with hard-coded settings.

**See [aether-console/README.md](./aether-console/README.md) for full documentation.**

## Quick Start

```powershell
cd aether-console
.\scripts\install_deps.ps1
.\scripts\run_dev.ps1
```

## Integration with Aether Project

**Current:** Development tool for ESP32-CAM configuration  
**Future:** Physical "eyes" mounted to robotic arm, streaming to AI assistant

[← Back to Main Project](../README.md)
