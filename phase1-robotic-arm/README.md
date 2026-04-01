# Phase 1: Robotic Arm

A compact 5-DOF (5 Degrees of Freedom) robotic arm for desktop manipulation. This phase serves as the physical interaction component of the larger Aether project.

## 🎯 Original Design Credit

**This robotic arm is based on the excellent work of Kelton from "Build Some Stuff"**

- **Original Designer:** Kelton (Build Some Stuff)
- **Original Design:** [Compact Robot Arm on Printables](https://www.printables.com/model/818975-compact-robot-arm-arduino-3d-printed)
- **Assembly Tutorial:** [YouTube Assembly Guide](https://youtu.be/AIsVlgopqJc)

**All original STL files, design work, and base Arduino code are credited to Kelton.** This phase documents the build process, modifications made, and future improvement plans.

## Project Overview

This build started with Kelton's original design and was:
1. **Printed initially in PLA** for prototyping and testing
2. **Rebuilt in PETG-CF** for improved strength and durability
3. **Modified** to accommodate different power connections and switches
4. **Successfully assembled and tested** - currently operational

## What Was Modified

### My Modifications
- **Power connections** - Adapted the design to work with different power supply connectors
- **Switch placement/design** - Modified to accommodate different switch types
- **Material choice** - Rebuilt from PLA to PETG-CF for better mechanical properties

### What Remains Original (Kelton's Design)
- Core mechanical design and structure
- Servo mounting solutions
- Gear ratios and kinematics
- Arduino control code (base version)
- Overall arm architecture

## Build Details

### Materials Used

**Initial Prototype:**
- PLA filament
- Used for testing fit and function

**Current Build:**
- PETG-CF (Carbon Fiber reinforced PETG)
- Better strength and heat resistance
- More rigid for precise movements

### Hardware Components
- 5x Servo motors (gripper, wrist, elbow, shoulder, base)
- Adafruit PCA9685 16-Channel PWM Servo Driver
- 4x Potentiometers (for manual control)
- 1x Push button (gripper control)
- Arduino Uno
- Power supply (modified connection type)
- Various screws and hardware
- Modified switches

### Electronics
- Control system uses potentiometers for manual positioning
- Servo driver board handles PWM signals
- Button control for gripper open/close
- 5-second startup delay for controller positioning

## Directory Structure

```
phase1-robotic-arm/
├── README.md (this file)
├── arduino/
│   └── Compact_Robot_Arm_Code.ino (Kelton's base code)
└── 3d-models/
    ├── original/
    │   └── Robot+Arm.3mf (Original slicer project)
    └── modified/
        ├── Robotic Arm Compact-SRU.3mf (Modified version with power/switch changes)
        └── Gears.3mf (Gear components)
```

## Current Status

✅ **Completed:**
- Initial PLA prototype printed and tested
- Full rebuild in PETG-CF completed
- Power and switch modifications implemented
- Arm is functional and operational

⏳ **In Progress:**
- Fine-tuning and calibration
- Testing under various loads

## Future Improvements

This arm is functional but has room for significant upgrades:

### Planned Enhancements
1. **Stepper Motor Conversion**
   - Replace servo motors with stepper motors
   - Enable precise position feedback and control
   - Allow for programmable movement sequences

2. **Cycloidal Drive Integration**
   - Implement cycloidal gear reduction
   - Achieve smoother, more precise motion
   - Increase torque while reducing backlash

3. **Computer Control**
   - Move beyond manual potentiometer control
   - Enable programmatic movement via PC
   - Prepare for AI integration (Phase 3)

4. **Vision System Integration**
   - Connect with Phase 2 (ESP32-CAM vision)
   - Enable visually-guided manipulation
   - Object recognition and targeting

## How to Build

### Prerequisites
- 3D Printer capable of printing PETG-CF (or PLA for prototyping)
- Basic soldering skills
- Arduino IDE
- Wire and basic electronics tools

### Steps
1. **Print the parts**
   - Use files from `3d-models/modified/` for the updated version
   - Or use Kelton's original files from [Printables](https://www.printables.com/model/818975-compact-robot-arm-arduino-3d-printed)
   - Recommended: PETG-CF for final build, PLA for testing

2. **Gather components**
   - 5x servos (check Kelton's BOM for specifications)
   - Adafruit PCA9685 servo driver
   - 4x potentiometers
   - 1x push button
   - Arduino Uno
   - Power supply and cables
   - Screws and hardware

3. **Assemble the arm**
   - Follow Kelton's excellent [assembly tutorial on YouTube](https://youtu.be/AIsVlgopqJc)
   - Note: Power connections and switches may differ based on modifications

4. **Upload the code**
   - Install Adafruit PWM Servo Driver library in Arduino IDE
   - Upload `Compact_Robot_Arm_Code.ino` to Arduino Uno
   - Adjust potentiometer mappings if needed

5. **Test and calibrate**
   - Power on and test each joint
   - Adjust servo limits in code if necessary
   - Fine-tune potentiometer ranges for smooth control

## Code Overview

The Arduino code (`Compact_Robot_Arm_Code.ino`) provides:
- Potentiometer-based manual control for 4 joints (base, shoulder, elbow, wrist)
- Button control for gripper (open/close)
- PWM servo control via Adafruit PCA9685 board
- 5-second startup delay to position controller before activation

## Lessons Learned

1. **PLA is fine for prototyping** but PETG-CF provides much better rigidity for final builds
2. **Power supply matters** - Ensure adequate current for all servos under load
3. **Gear backlash** is noticeable with standard servos - cycloidal drives will help
4. **Manual control is limiting** - computer control will be essential for AI integration

## Integration with Aether Project

This robotic arm will eventually serve as the "hands" of the Aether system:
- **Phase 2 (Vision)** will give it "eyes" to see objects
- **Phase 3 (AI Assistant)** will give it a "brain" to make decisions
- Together, they'll enable autonomous desktop tasks

## Resources

- **Original Design:** [Kelton's Printables Page](https://www.printables.com/model/818975-compact-robot-arm-arduino-3d-printed)
- **Assembly Guide:** [Kelton's YouTube Tutorial](https://youtu.be/AIsVlgopqJc)
- **Adafruit PCA9685 Library:** Available through Arduino Library Manager
- **Servo Specs:** See Kelton's BOM for recommended servos

## Attribution

**Original Design:** All credit for the base design, STL files, and Arduino code goes to Kelton from "Build Some Stuff". This project builds upon his excellent work with modifications for specific hardware and future enhancement plans.

**Modifications:** Power connections, switch integration, material selection, and future upgrade planning by builtbycodyrd.

---

**Status:** Phase 1 is operational and functional. Future enhancements (stepper motors, cycloidal drives) planned for improved precision and computer control.

[← Back to Main Project](../README.md)
