from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoardProfile:
    key: str
    label: str
    notes: str


# Product direction and session handoff note:
# - These are the board profiles surfaced in the pairing UI.
# - The app should recommend one automatically where possible, but still let the
#   user override it before flashing.
# - Not every board listed here is truly flash-ready yet; support status is
#   determined by config/firmware_manifest.json and the presence of bundled
#   firmware assets.
# - The first concrete firmware-source target is currently AI Thinker ESP32-CAM.
# - Other boards stay visible in the UI so users can see the roadmap, but they
#   should remain marked in progress until real firmware packages exist and have
#   been validated.
# - Future sessions should update this comment block if the support set changes.
BOARD_PROFILES: list[BoardProfile] = [
    BoardProfile("ai_thinker", "AI Thinker ESP32-CAM", "Most common ESP32-CAM module."),
    BoardProfile("m5stack_unitcam", "M5Stack UnitCam", "UnitCam and related M5 variants."),
    BoardProfile("m5stack_esp32cam", "M5Stack ESP32CAM", "Legacy M5Stack ESP32 camera module."),
    BoardProfile("esp_eye", "ESP-EYE", "Espressif ESP-EYE development board."),
    BoardProfile("wrover_kit", "ESP32 Wrover Kit", "Wrover kit with camera support."),
    BoardProfile("ttgo_t_journal", "TTGO T-Journal", "TTGO T-Journal camera board."),
    BoardProfile("xiao_esp32s3_sense", "Seeed XIAO ESP32S3 Sense", "ESP32-S3 board with Sense camera addon."),
    BoardProfile("firebeetle_esp32s3", "FireBeetle 2 ESP32-S3", "ESP32-S3 camera-capable board."),
]


def board_profile_map() -> dict[str, BoardProfile]:
    return {profile.key: profile for profile in BOARD_PROFILES}


def board_labels() -> list[str]:
    return [profile.label for profile in BOARD_PROFILES]


def profile_by_key(key: str) -> BoardProfile:
    return board_profile_map().get(key, BOARD_PROFILES[0])


def profile_by_label(label: str) -> BoardProfile:
    for profile in BOARD_PROFILES:
        if profile.label == label:
            return profile
    return BOARD_PROFILES[0]


def detect_profile_from_port(description: str, hwid: str, manufacturer: str) -> tuple[BoardProfile, str]:
    haystack = f"{description} {hwid} {manufacturer}".lower()
    if "xiao" in haystack or "esp32s3" in haystack:
        profile = profile_by_key("xiao_esp32s3_sense")
        return profile, f"Detected USB descriptor hints for {profile.label}."
    if "firebeetle" in haystack:
        profile = profile_by_key("firebeetle_esp32s3")
        return profile, f"Detected USB descriptor hints for {profile.label}."
    if "m5stack" in haystack or "unitcam" in haystack:
        profile = profile_by_key("m5stack_unitcam")
        return profile, f"Detected USB descriptor hints for {profile.label}."
    if "esp-eye" in haystack or "esp eye" in haystack:
        profile = profile_by_key("esp_eye")
        return profile, f"Detected USB descriptor hints for {profile.label}."
    if "wrover" in haystack:
        profile = profile_by_key("wrover_kit")
        return profile, f"Detected USB descriptor hints for {profile.label}."
    if "ttgo" in haystack or "t-journal" in haystack:
        profile = profile_by_key("ttgo_t_journal")
        return profile, f"Detected USB descriptor hints for {profile.label}."
    profile = profile_by_key("ai_thinker")
    return profile, f"Exact board auto-detection is limited over serial. {profile.label} is the recommended default."
