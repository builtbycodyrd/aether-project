"""
ESP32 camera control API helper.

Purpose:
- Define the camera settings surface shown in the desktop app.
- Translate local config values into ESP32 /control?var=...&val=... HTTP calls.

Why this file matters:
- The first iteration only exposed a few settings.
- This expanded version is intended to make the app feel more complete for camera tuning.

Known limitation:
- Settings are currently sent one request at a time, which can contribute to timeouts on some boards.
- If future work focuses on performance/reliability, batching, retries, or pacing should be considered.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import urlopen


RESOLUTION_MAP: dict[str, int] = {
    "QQVGA": 0,
    "QCIF": 1,
    "HQVGA": 2,
    "QVGA": 3,
    "CIF": 4,
    "VGA": 5,
    "SVGA": 6,
    "XGA": 7,
    "SXGA": 8,
    "UXGA": 9,
}


@dataclass(frozen=True)
class CameraControlSpec:
    key: str
    label: str
    var_name: str
    minimum: int
    maximum: int
    default: int | bool
    widget: str


CAMERA_CONTROL_SPECS: list[CameraControlSpec] = [
    CameraControlSpec("jpeg_quality", "JPEG Quality", "quality", 10, 63, 12, "slider"),
    CameraControlSpec("brightness", "Brightness", "brightness", -2, 2, 0, "slider"),
    CameraControlSpec("contrast", "Contrast", "contrast", -2, 2, 0, "slider"),
    CameraControlSpec("saturation", "Saturation", "saturation", -2, 2, 0, "slider"),
    CameraControlSpec("sharpness", "Sharpness", "sharpness", -2, 2, 0, "slider"),
    CameraControlSpec("special_effect", "Special Effect", "special_effect", 0, 6, 0, "slider"),
    CameraControlSpec("awb", "Auto White Balance", "awb", 0, 1, True, "checkbox"),
    CameraControlSpec("awb_gain", "AWB Gain", "awb_gain", 0, 1, True, "checkbox"),
    CameraControlSpec("wb_mode", "White Balance Mode", "wb_mode", 0, 4, 0, "slider"),
    CameraControlSpec("aec", "Auto Exposure", "aec", 0, 1, True, "checkbox"),
    CameraControlSpec("aec2", "AEC DSP", "aec2", 0, 1, False, "checkbox"),
    CameraControlSpec("ae_level", "AE Level", "ae_level", -2, 2, 0, "slider"),
    CameraControlSpec("agc", "Auto Gain", "agc", 0, 1, True, "checkbox"),
    CameraControlSpec("agc_gain", "AGC Gain", "agc_gain", 0, 30, 0, "slider"),
    CameraControlSpec("gainceiling", "Gain Ceiling", "gainceiling", 0, 6, 0, "slider"),
    CameraControlSpec("bpc", "Black Pixel Correction", "bpc", 0, 1, False, "checkbox"),
    CameraControlSpec("wpc", "White Pixel Correction", "wpc", 0, 1, True, "checkbox"),
    CameraControlSpec("raw_gma", "Raw Gamma", "raw_gma", 0, 1, True, "checkbox"),
    CameraControlSpec("lenc", "Lens Correction", "lenc", 0, 1, True, "checkbox"),
    CameraControlSpec("dcw", "Downsize Enable", "dcw", 0, 1, True, "checkbox"),
    CameraControlSpec("colorbar", "Color Bar", "colorbar", 0, 1, False, "checkbox"),
    CameraControlSpec("horizontal_flip", "Horizontal Flip", "hmirror", 0, 1, False, "checkbox"),
    CameraControlSpec("vertical_flip", "Vertical Flip", "vflip", 0, 1, False, "checkbox"),
]


class CameraControlError(RuntimeError):
    pass


def send_control(camera_base_url: str, var_name: str, value: int) -> None:
    base = camera_base_url.rstrip("/")
    params = urlencode({"var": var_name, "val": value})
    url = f"{base}/control?{params}"
    try:
        with urlopen(url, timeout=5) as response:
            status = getattr(response, "status", 200)
            if status >= 400:
                raise CameraControlError(f"Camera returned HTTP {status} for {var_name}")
            response.read()
    except Exception as exc:
        raise CameraControlError(str(exc)) from exc


def apply_camera_settings(cfg: dict) -> None:
    send_control(cfg["camera_base_url"], "framesize", RESOLUTION_MAP[cfg["resolution"]])
    for spec in CAMERA_CONTROL_SPECS:
        raw_value = cfg.get(spec.key, spec.default)
        value = 1 if raw_value is True else 0 if raw_value is False else int(raw_value)
        send_control(cfg["camera_base_url"], spec.var_name, value)

