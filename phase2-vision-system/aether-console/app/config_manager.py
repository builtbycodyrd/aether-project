from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from pathlib import Path


# The reference repo used a central config helper to make source and packaged
# execution consistent. This keeps that pattern, but stores mutable data in
# LOCALAPPDATA so installed builds can pair cameras and cache models safely.
def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def user_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / "AetherConsole"
    return app_root() / ".localdata"


def default_config_path() -> Path:
    return app_root() / "config" / "default_config.json"


def firmware_manifest_path() -> Path:
    return app_root() / "config" / "firmware_manifest.json"


def firmware_assets_dir() -> Path:
    return app_root() / "firmware_assets"


def config_path() -> Path:
    return user_data_dir() / "config" / "aether_console.json"


def firmware_workspace() -> Path:
    path = user_data_dir() / "firmware"
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> dict:
    # Be tolerant of UTF-8 BOM because Windows editors and some scripts may
    # write JSON with BOM even though json.loads expects plain UTF-8 by default.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_default_config() -> dict:
    return read_json(default_config_path())


def load_firmware_manifest() -> dict:
    return read_json(firmware_manifest_path())


def firmware_board_entry(board_key: str) -> dict:
    return load_firmware_manifest().get("boards", {}).get(board_key, {})


def firmware_support_level(board_key: str) -> str:
    return firmware_board_entry(board_key).get("support_level", "in_progress")


def firmware_support_badge(board_key: str) -> str:
    return "Fully Supported" if firmware_support_level(board_key) == "fully_supported" else "In Progress"


def load_config() -> dict:
    cfg = deepcopy(load_default_config())
    path = config_path()
    if path.exists():
        try:
            saved = read_json(path)
        except Exception:
            saved = {}
        cfg.update(saved)
    return cfg


def save_config(cfg: dict) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return path


def models_dir() -> Path:
    directory = user_data_dir() / "models"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def installed_model_paths() -> list[Path]:
    directory = models_dir()
    return sorted(directory.glob("*.pt")) + sorted(directory.glob("*.onnx"))


def find_model_path(preferred_name: str) -> str:
    for path in installed_model_paths():
        if path.name == preferred_name:
            return str(path)
    return ""


def active_camera(cfg: dict) -> dict | None:
    selected_id = cfg.get("selected_camera_id", "")
    for camera in cfg.get("paired_cameras", []):
        if camera.get("id") == selected_id:
            return camera
    return None
