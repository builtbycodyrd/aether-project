"""
Serial pairing and firmware flashing for ESP32-CAM devices.

Purpose:
- Discover likely ESP32 serial devices.
- Recommend a board profile and allow the UI to override it.
- Flash bundled firmware packages with esptool instead of depending on Arduino CLI at runtime.

Current project state:
- The runtime path now targets a production-style flasher architecture.
- The repo includes a firmware manifest describing intended supported boards and whether each one is fully supported or still in progress.
- The first concrete firmware-source target is AI Thinker ESP32-CAM.
- Actual per-board production firmware binaries are not yet committed, so pairing currently
  reports a missing-package or in-progress state until those assets are added.

Known risk areas:
- True end-user reliability depends on validated firmware assets for each board profile.
- Wi-Fi provisioning is part of the intended firmware contract, but the bundled package format
  still needs the final asset pipeline to make that real.
- Until assets exist, this module is architecture-complete but not hardware-complete.

Future-session rule:
- If the pairing architecture, supported board list, or package format changes, update this
  module header and the handoff docs before the session ends.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal

from board_profiles import BOARD_PROFILES, detect_profile_from_port, profile_by_key
from config_manager import (
    firmware_assets_dir,
    firmware_support_badge,
    firmware_support_level,
    firmware_workspace,
    load_firmware_manifest,
)

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None


@dataclass
class SerialPortCandidate:
    device: str
    description: str
    manufacturer: str
    hwid: str
    board_key: str
    board_label: str
    detection_note: str


@dataclass
class CommandResult:
    returncode: int
    output: str


def load_manifest() -> dict:
    return load_firmware_manifest()


def firmware_package_status(board_key: str) -> tuple[bool, str]:
    manifest = load_manifest()
    board = manifest.get("boards", {}).get(board_key)
    if not board:
        return False, "No firmware manifest entry exists for this board."
    if not board.get("supported", False):
        return False, "This board is not marked as supported in the firmware manifest."
    if firmware_support_level(board_key) != "fully_supported":
        return False, f"{firmware_support_badge(board_key)}: firmware packaging for this board is still in progress."
    assets_root = firmware_assets_dir()
    missing = []
    for item in board.get("flash_files", []):
        candidate = assets_root / item["path"]
        if not candidate.exists():
            missing.append(str(candidate.name))
    if missing:
        return False, f"Firmware package missing file(s): {', '.join(missing)}"
    return True, "Bundled firmware package is present."


def package_flash_plan(board_key: str) -> list[tuple[str, str]]:
    manifest = load_manifest()
    board = manifest.get("boards", {}).get(board_key, {})
    assets_root = firmware_assets_dir()
    plan: list[tuple[str, str]] = []
    for item in board.get("flash_files", []):
        plan.append((item["offset"], str(assets_root / item["path"])))
    return plan


class PairingWorker(QThread):
    log_message = pyqtSignal(str)
    pairing_finished = pyqtSignal(dict)

    def __init__(self, port: str, board_key: str, camera_name: str, wifi_ssid: str, wifi_password: str):
        super().__init__()
        self.port = port
        self.board_key = board_key
        self.camera_name = camera_name
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password

    def run(self) -> None:
        profile = profile_by_key(self.board_key)
        hostname = slugify(self.camera_name) or "aether-camera"

        package_ok, package_message = firmware_package_status(profile.key)
        if not package_ok:
            self.pairing_finished.emit(
                {
                    "ok": False,
                    "message": "Pairing cannot start because the firmware package is missing or not yet ready.",
                    "details": package_message,
                    "stream_url": f"http://{hostname}.local:81/stream",
                    "camera_base_url": f"http://{hostname}.local",
                }
            )
            return

        self.log_message.emit(f"Preparing bundled firmware flash for {profile.label} on {self.port}")
        workdir = firmware_workspace()
        workdir.mkdir(parents=True, exist_ok=True)
        config_blob = {
            "camera_name": self.camera_name,
            "wifi_ssid": self.wifi_ssid,
            "wifi_password": self.wifi_password,
            "hostname": hostname,
            "board_key": profile.key,
        }
        config_path = workdir / "pairing_runtime_config.json"
        import json
        config_path.write_text(json.dumps(config_blob, indent=2), encoding="utf-8")
        self.log_message.emit(f"Wrote pairing metadata to {config_path}")

        command = [
            sys.executable,
            "-m",
            "esptool",
            "--chip",
            chip_family_for_profile(profile.key),
            "--port",
            self.port,
            "--baud",
            baud_for_profile(profile.key),
            "write_flash",
            "-z",
        ]
        for offset, path in package_flash_plan(profile.key):
            command.extend([offset, path])

        result = run_command(command)
        self.log_message.emit(result.output)

        if result.returncode != 0:
            self.pairing_finished.emit(
                {
                    "ok": False,
                    "message": "Firmware flashing failed.",
                    "details": result.output,
                    "stream_url": f"http://{hostname}.local:81/stream",
                    "camera_base_url": f"http://{hostname}.local",
                }
            )
            return

        self.pairing_finished.emit(
            {
                "ok": True,
                "message": f"Pairing completed for {self.camera_name}.",
                "details": "Bundled firmware flashed successfully. Ensure the camera joins Wi-Fi before starting preview.",
                "stream_url": f"http://{hostname}.local:81/stream",
                "camera_base_url": f"http://{hostname}.local",
            }
        )


def list_serial_candidates() -> list[SerialPortCandidate]:
    if list_ports is None:
        return []
    candidates: list[SerialPortCandidate] = []
    for port in list_ports.comports():
        description = getattr(port, "description", "") or "Unknown serial device"
        manufacturer = getattr(port, "manufacturer", "") or "Unknown manufacturer"
        hwid = getattr(port, "hwid", "") or ""
        profile, note = detect_profile_from_port(description, hwid, manufacturer)
        candidates.append(
            SerialPortCandidate(
                device=port.device,
                description=description,
                manufacturer=manufacturer,
                hwid=hwid,
                board_key=profile.key,
                board_label=profile.label,
                detection_note=note,
            )
        )
    return candidates


def run_command(command: list[str]) -> CommandResult:
    process = subprocess.run(command, capture_output=True, text=True)
    output = (process.stdout or "") + (process.stderr or "")
    return CommandResult(returncode=process.returncode, output=output.strip())


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return cleaned.strip("-")


def chip_family_for_profile(board_key: str) -> str:
    if "esp32s3" in board_key or board_key == "xiao_esp32s3_sense":
        return "esp32s3"
    return "esp32"


def baud_for_profile(board_key: str) -> str:
    return "460800" if board_key == "xiao_esp32s3_sense" else "921600"
