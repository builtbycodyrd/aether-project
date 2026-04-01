# Aether Project

A long-term, multi-phase project to build a seamless AI-powered smart desktop companion inspired by Tony Stark's DUMMY robot. The vision is to create a unified system combining robotics, computer vision, and AI assistance — all working together as one intelligent desktop assistant.

## Project Vision

**Aether** is designed to be more than just individual components. Each phase builds upon the previous one, eventually converging into a single cohesive system that can:
- Physically interact with the workspace (robotic manipulation)
- See and understand its environment (computer vision)
- Process information and assist intelligently (AI assistant)
- Operate autonomously while remaining responsive to user commands

Think of it as bringing a piece of sci-fi into reality — a desktop companion that's both functional and futuristic.

## Multi-Phase Architecture

This project is being built in phases, with each phase designed to eventually integrate with the others:

### Phase 1: Robotic Arm ✅ In Progress
A compact 5-DOF robotic arm for physical desktop interaction. Started as a 3D-printed PLA prototype, now rebuilt in PETG-CF with plans for precision upgrades.

**Status:** Built and operational. Future improvements planned (stepper motors + cycloidal drives).

📁 [View Phase 1 Details →](./phase1-robotic-arm/)

---

### Phase 2: Computer Vision System 🔜 Planned
ESP32-CAM-based vision system for environmental awareness and object recognition.

**Status:** Planned. Will enable the arm to "see" and respond to its environment.

📁 [View Phase 2 Details →](./phase2-vision-system/)

---

### Phase 3: AI Assistant (Aether) 🔜 Planned
PC-embedded AI assistant that serves as the brain of the system, coordinating between vision and manipulation.

**Status:** Planned. Will unify all phases into one intelligent system.

📁 [View Phase 3 Details →](./phase3-ai-assistant/)

---

## Long-Term Integration

Once all phases are complete, the system will function as:

```
┌─────────────────────────────────────────────────┐
│             Aether AI Assistant                 │
│         (Brain - PC Embedded)                   │
└────────────┬───────────────────┬────────────────┘
             │                   │
    ┌────────▼────────┐  ┌───────▼────────┐
    │  Vision System  │  │  Robotic Arm   │
    │   (ESP32-CAM)   │  │   (Physical)   │
    │   "The Eyes"    │  │  "The Hands"   │
    └─────────────────┘  └────────────────┘
```

The AI will:
1. **See** through the ESP32-CAM vision system
2. **Think** and process through the PC-embedded assistant
3. **Act** through the robotic arm

All working together seamlessly as one unified desktop companion.

## Current Status

- ✅ **Phase 1** - Robotic arm built and operational
- ⏳ **Phase 2** - Vision system in planning
- ⏳ **Phase 3** - AI assistant in planning
- ⏳ **Integration** - Future milestone

## Project Philosophy

This project prioritizes:
- **Modularity** - Each phase can work independently while being designed for integration
- **Iteration** - Continuous improvement and refinement (e.g., PLA → PETG-CF → stepper motors)
- **Open Documentation** - Sharing the journey, crediting sources, and building on others' work
- **Practical Functionality** - Not just for show, but genuinely useful on a desktop

## Getting Started

Each phase has its own detailed README with:
- Component lists
- Build instructions
- Code and configuration files
- Lessons learned and future improvements

Start with Phase 1 to see how the foundation was built, or explore the planned phases to understand the full vision.

## Inspiration

Inspired by Tony Stark's DUMMY robot — the loyal, semi-autonomous robotic assistant. While DUMMY had personality through subtle movements and "behavior," this project aims to bring that concept to life with real AI, vision, and manipulation capabilities.

## License

See individual phase folders for attribution and licensing information. This project builds upon the work of others (with proper credit given) and includes original modifications and additions.

---

**Note:** This is an ongoing project. Documentation, code, and designs will be updated as each phase progresses. Check individual phase folders for the most current status.
