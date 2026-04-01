# Phase 3: AI Assistant (Aether)

**Status:** ✅ Core System Functional | ⏳ Voice System Being Refined

The brain of the Aether Project - a comprehensive AI-powered personal assistant with voice interaction, task management, and integration capabilities.

## Overview

**Aether** is a desktop AI assistant built with Claude Sonnet 4.5, designed as the central intelligence that will eventually coordinate the robotic arm (Phase 1) and vision system (Phase 2).

**Built with:** Claude Code CLI (Opus 4.5)

## Architecture

Multi-service system with FastAPI backend, MCP servers, Tauri desktop shell, and Progressive Web App for mobile.

### Services (Windows Services via NSSM)
- **Backend** (port 8000) - Main FastAPI server
- **7 MCP Servers** (ports 8010-8016) - Filesystem, Terminal, Email, Browser, Screen, Tasks, 3D

## Current Status

### ✅ Working
- Aether branding with purple theme and animated 3D orb
- Claude Sonnet 4.5 chat integration
- All 7 MCP servers healthy
- File system access with safety gates
- Task/reminder system
- Voice capture (mic button works, orb reacts)
- Whisper transcription working
- TTS synthesis functional
- Desktop shell (Tauri) runs stably
- PWA available for mobile

### ⚠️ Known Issues (Being Fixed)
1. **Voice transcription buffer too large** - Accumulates 2+ minutes causing hangs
   - Fix: Cap at 10 seconds, add timeouts
2. **Wake word still says "Hey Jarvis"** - Needs Amendment 4 implementation
   - Fix: Update to "Hey Aether"
3. **Notifications broken** - Shell_NotifyIconW fails (harmless, suppressed)

### ⏳ Not Yet Implemented
- AMENDMENT_4_AETHER_REBRAND - Wake words, system prompt
- AMENDMENT_5_SPEED - Performance optimizations

### 🔮 Future Plans
- iPhone via Tailscale PWA
- Email credentials in Settings UI
- Better voice variety (Kokoro ONNX)
- Proper Tauri release build
- Proactive notifications (calendar, email, D2L alerts)
- **Integration with Phase 1 & 2** - Control arm, process vision

## Features

**AI Models:**
- Claude Sonnet 4.5 (primary)
- Ollama local models (llama3.1:8b, phi3:mini, qwen2.5-coder:14b, llava:7b)
- Automatic routing based on task

**Voice Interaction:**
- Push-to-talk and wake word detection
- Whisper transcription
- TTS synthesis
- Animated purple orb visual feedback

**MCP Servers:**
- Filesystem - File operations with confirmation
- Terminal - Safe command execution
- Email - Yahoo, Gmail, SRU integration
- Browser - D2L scraping, web fetch
- Screen - Screenshot + vision analysis
- Tasks - Calendar and assignments
- 3D - Orb rendering

**Memory System:**
- ChromaDB vector database
- Long-term conversation memory
- Context-aware responses

**Interfaces:**
- Desktop shell (Tauri + React + Three.js)
- Progressive Web App (mobile-friendly)
- iPhone installable via Safari

## Tech Stack

**Backend:** FastAPI, Claude API, Ollama, Whisper, ChromaDB, SQLite  
**Desktop:** Tauri 2.0, React 19, TypeScript, Three.js, TailwindCSS  
**PWA:** React 19, Vite, Service Workers  
**Deployment:** NSSM Windows services

## Management

Start services: `C:\assistant\scripts\start-services.bat`  
Stop services: `C:\assistant\scripts\stop-services.bat`  
Check status: `C:\assistant\scripts\status-services.bat`  
Health check: `http://localhost:8000/health`

## Documentation

See `docs/` folder for comprehensive documentation:
- Architecture specifications
- Amendment documents (rebrand, voice, speed optimizations)
- Build specifications
- Voice setup guides

## Integration with Aether Project

**Current:** Standalone personal assistant  
**Future:** Central brain coordinating vision (Phase 2) and manipulation (Phase 1)

**Planned:**
- Voice control: "Aether, pick up that pen"
- Process ESP32-CAM vision feed
- Guide robotic arm with visual input
- Autonomous decision-making
- Proactive assistance

## Files Included

- `README.md` - This file
- `ASSISTANT_README.md` - Original system README
- `docs/` - 12 documentation files including amendments
- `backend-sample/` - Python requirements.txt
- `shell-sample/` - Node package.json
- `scripts/` - Service management scripts

**Note:** Full source code remains in `C:\assistant` on development machine. This repo contains documentation and architecture for reference.

---

**Phase 3 Status:** Core functionality complete. Voice latency issues being resolved. Ready for future Phase 1/2 integration.

[← Back to Main Project](../README.md)
