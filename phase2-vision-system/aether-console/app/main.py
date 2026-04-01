"""
Aether Console main desktop window.

Project intent:
- This app is meant to be a professional ESP32-CAM onboarding and tuning tool.
- USB/serial is used for pairing and firmware flashing.
- Normal runtime preview and control happen over Wi-Fi using the camera's MJPEG stream and
  HTTP /control API.
- Optional YOLO detection is available, with model download handled on demand.
- Pairing is being moved toward bundled firmware packages plus esptool instead of runtime Arduino tooling.

What works so far:
- Multi-tab PyQt6 desktop UI for setup, preview, camera controls, detection, and logs.
- Paired camera persistence in the local JSON config.
- Detection model selection with default-on-install yolov8n and on-demand heavier models.
- Preview worker hookup and camera control dispatch to the ESP32 HTTP API.
- Pairing flow UI wiring to a background worker.
- Board package presence can now be checked before attempting a flash.

What still needs real-world validation:
- The serial pairing flow has only been syntax-validated, not hardware-validated.
- Auto-detected board recommendations are heuristic and may need refinement.
- Bundled firmware assets are not yet present in this repository, so pairing will currently stop with a clear missing-package message.
- Camera control timeouts still need tuning; the user reported occasional timeouts when applying settings.

Guidance for a future Codex session:
- Start by reading CONTEXT.md and app/pairing.py.
- When the session is roughly 30% from its remaining context budget, update CONTEXT.md and these module header comments so the handoff stays current.
- If pairing fails, inspect the exact flasher output first.
- If preview fails after successful pairing, verify the saved stream/control URLs and network reachability.
- Keep the app focused on ESP32-CAM class devices; do not drift into robotic-arm features.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from board_profiles import BOARD_PROFILES, profile_by_key
from camera_api import CAMERA_CONTROL_SPECS, RESOLUTION_MAP, apply_camera_settings
from config_manager import active_camera, find_model_path, firmware_support_badge, load_config, save_config
from detection import OptionalDetector
from model_manager import (
    DEFAULT_MODEL,
    RECOMMENDED_MODELS,
    display_names,
    display_to_model_name,
    model_install_state,
    resolve_model_path,
)
from pairing import PairingWorker, firmware_package_status, list_serial_candidates
from stream_worker import StreamWorker


def slider_row(minimum: int, maximum: int, value: int) -> tuple[QSlider, QLabel]:
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setValue(value)
    value_label = QLabel(str(value))
    value_label.setMinimumWidth(40)
    slider.valueChanged.connect(lambda current: value_label.setText(str(current)))
    return slider, value_label


class AetherConsoleWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Aether Console")
        self.setMinimumSize(1440, 920)

        self.cfg = load_config()
        self.worker: StreamWorker | None = None
        self.pair_worker: PairingWorker | None = None
        self.detector_probe = OptionalDetector()
        self.class_checks: dict[str, QCheckBox] = {}
        self.camera_control_widgets: dict[str, object] = {}

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        self._build_setup_tab()
        self._build_preview_tab()
        self._build_camera_tab()
        self._build_detection_tab()
        self._build_logs_tab()

        self._wire_events()
        self._apply_config_to_ui()
        self.refresh_serial_ports()
        self.refresh_models()
        self.refresh_paired_cameras()
        self._refresh_model_status()
        self._refresh_setup_banner()

    def _wire_events(self) -> None:
        self.refresh_ports_button.clicked.connect(self.refresh_serial_ports)
        self.port_combo.currentIndexChanged.connect(self.on_port_selection_changed)
        self.pair_button.clicked.connect(self.start_pairing)
        self.refresh_cameras_button.clicked.connect(self.refresh_paired_cameras)
        self.paired_camera_combo.currentIndexChanged.connect(self.on_paired_camera_changed)
        self.start_button.clicked.connect(self.start_preview)
        self.stop_button.clicked.connect(self.stop_preview)
        self.save_button.clicked.connect(self.save_current_config)
        self.apply_all_button.clicked.connect(self.apply_camera_settings_now)
        self.restore_defaults_button.clicked.connect(self.restore_camera_defaults)
        self.model_reload_button.clicked.connect(self.refresh_models)
        self.model_browse_button.clicked.connect(self.choose_model_file)
        self.download_model_button.clicked.connect(self.download_selected_model)
        self.download_all_models_button.clicked.connect(self.download_all_models)
        self.model_combo.currentTextChanged.connect(lambda _value: self._refresh_model_status())
        self.device_combo.currentTextChanged.connect(lambda _value: self._refresh_model_status())

    def _build_setup_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.setup_banner = QLabel()
        self.setup_banner.setWordWrap(True)
        self.setup_banner.setStyleSheet("font-size:16px; font-weight:600;")
        layout.addWidget(self.setup_banner)

        paired_box = QGroupBox("Paired Cameras")
        paired_form = QFormLayout(paired_box)
        self.paired_camera_combo = QComboBox()
        self.refresh_cameras_button = QPushButton("Refresh Paired Cameras")
        self.active_camera_label = QLabel("No paired camera selected.")
        paired_form.addRow("Camera", self.paired_camera_combo)
        paired_form.addRow("", self.refresh_cameras_button)
        paired_form.addRow("Active", self.active_camera_label)
        layout.addWidget(paired_box)

        pair_box = QGroupBox("Pair Camera")
        pair_form = QFormLayout(pair_box)
        self.camera_name_edit = QLineEdit()
        self.camera_name_edit.setPlaceholderText("Workshop Camera")
        self.wifi_ssid_edit = QLineEdit()
        self.wifi_password_edit = QLineEdit()
        self.wifi_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.port_combo = QComboBox()
        self.refresh_ports_button = QPushButton("Scan Serial Ports")
        self.detected_board_label = QLabel("No serial device selected.")
        self.board_override_combo = QComboBox()
        for profile in BOARD_PROFILES:
            self.board_override_combo.addItem(f"{profile.label} [{firmware_support_badge(profile.key)}]", profile.key)
        self.pair_button = QPushButton("Pair Camera")
        self.pairing_status_label = QLabel("Connect an ESP32-CAM and scan serial ports.")
        self.pairing_status_label.setWordWrap(True)
        pair_form.addRow("Camera Name", self.camera_name_edit)
        pair_form.addRow("Wi-Fi SSID", self.wifi_ssid_edit)
        pair_form.addRow("Wi-Fi Password", self.wifi_password_edit)
        pair_form.addRow("Serial Device", self.port_combo)
        pair_form.addRow("", self.refresh_ports_button)
        pair_form.addRow("Detected Board", self.detected_board_label)
        pair_form.addRow("Board Choice", self.board_override_combo)
        pair_form.addRow("", self.pair_button)
        pair_form.addRow("Status", self.pairing_status_label)
        layout.addWidget(pair_box)
        layout.addStretch(1)

        self.tabs.addTab(tab, "Setup")
    def _build_preview_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        top_box = QGroupBox("Preview")
        top_form = QFormLayout(top_box)
        self.stream_url_edit = QLineEdit()
        self.camera_base_url_edit = QLineEdit()
        top_form.addRow("Stream URL", self.stream_url_edit)
        top_form.addRow("Camera Base URL", self.camera_base_url_edit)
        layout.addWidget(top_box)

        buttons = QHBoxLayout()
        self.start_button = QPushButton("Start Preview")
        self.stop_button = QPushButton("Stop Preview")
        self.stop_button.setEnabled(False)
        self.save_button = QPushButton("Save Config")
        self.apply_all_button = QPushButton("Apply Camera Settings")
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.apply_all_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.preview_label = QLabel("Preview is stopped.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(560)
        self.preview_label.setStyleSheet(
            "background:#10151c; color:#d8e0ea; border:1px solid #34404f; border-radius:12px;"
        )
        layout.addWidget(self.preview_label, stretch=1)

        self.connection_status = QLabel("Idle")
        self.stats_label = QLabel("FPS: 0.0 | Detections: 0")
        layout.addWidget(self.connection_status)
        layout.addWidget(self.stats_label)

        self.tabs.addTab(tab, "Preview")

    def _build_camera_tab(self) -> None:
        tab = QWidget()
        outer = QVBoxLayout(tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_host = QWidget()
        scroll_layout = QVBoxLayout(scroll_host)

        basics = QGroupBox("Core Camera Settings")
        basics_grid = QGridLayout(basics)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(list(RESOLUTION_MAP.keys()))
        basics_grid.addWidget(QLabel("Resolution"), 0, 0)
        basics_grid.addWidget(self.resolution_combo, 0, 1)
        scroll_layout.addWidget(basics)

        advanced = QGroupBox("Advanced Camera Controls")
        advanced_grid = QGridLayout(advanced)
        row = 0
        for spec in CAMERA_CONTROL_SPECS:
            if spec.widget == "checkbox":
                checkbox = QCheckBox(spec.label)
                self.camera_control_widgets[spec.key] = checkbox
                advanced_grid.addWidget(checkbox, row, 0, 1, 2)
            else:
                slider, value_label = slider_row(spec.minimum, spec.maximum, int(self.cfg.get(spec.key, spec.default)))
                self.camera_control_widgets[spec.key] = slider
                advanced_grid.addWidget(QLabel(spec.label), row, 0)
                advanced_grid.addWidget(slider, row, 1)
                advanced_grid.addWidget(value_label, row, 2)
            row += 1

        self.auto_apply_check = QCheckBox("Auto-apply camera settings on save")
        advanced_grid.addWidget(self.auto_apply_check, row, 0, 1, 3)
        scroll_layout.addWidget(advanced)

        actions = QHBoxLayout()
        self.restore_defaults_button = QPushButton("Restore Defaults")
        actions.addWidget(self.restore_defaults_button)
        actions.addStretch(1)
        scroll_layout.addLayout(actions)
        scroll_layout.addStretch(1)

        scroll.setWidget(scroll_host)
        outer.addWidget(scroll)
        self.tabs.addTab(tab, "Camera")

    def _build_detection_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("Detection")
        form = QFormLayout(box)
        self.detection_enabled_check = QCheckBox("Enable YOLO overlay")
        self.model_combo = QComboBox()
        self.model_browse_button = QPushButton("Use Custom Model")
        self.download_model_button = QPushButton("Download Selected Model")
        self.download_all_models_button = QPushButton("Download All Recommended Models")
        self.device_combo = QComboBox()
        self.device_combo.addItems(["Auto", "GPU", "CPU"])
        self.confidence_slider, self.confidence_value = slider_row(1, 99, int(float(self.cfg.get("confidence", 0.25)) * 100))
        self.iou_slider, self.iou_value = slider_row(1, 99, int(float(self.cfg.get("iou", 0.45)) * 100))
        self.img_size_spin = QSpinBox()
        self.img_size_spin.setRange(320, 1280)
        self.img_size_spin.setSingleStep(32)
        self.model_reload_button = QPushButton("Refresh Installed Models")
        self.model_status_label = QLabel("Detection idle.")
        self.model_status_label.setWordWrap(True)

        form.addRow("", self.detection_enabled_check)
        form.addRow("Model", self.model_combo)
        form.addRow("", self.model_browse_button)
        form.addRow("", self.download_model_button)
        form.addRow("", self.download_all_models_button)
        form.addRow("Device", self.device_combo)
        form.addRow("Confidence", self._host_slider(self.confidence_slider, self.confidence_value))
        form.addRow("IoU", self._host_slider(self.iou_slider, self.iou_value))
        form.addRow("Image Size", self.img_size_spin)
        layout.addWidget(box)
        layout.addWidget(self.model_reload_button)
        layout.addWidget(self.model_status_label)

        classes_box = QGroupBox("Classes")
        classes_layout = QVBoxLayout(classes_box)
        self.class_container = QWidget()
        self.class_layout = QVBoxLayout(self.class_container)
        classes_layout.addWidget(self.class_container)
        layout.addWidget(classes_box)
        layout.addStretch(1)

        self.tabs.addTab(tab, "Detection")

    def _build_logs_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        self.tabs.addTab(tab, "Logs")

    def _host_slider(self, slider: QSlider, value_label: QLabel) -> QWidget:
        host = QWidget()
        row = QHBoxLayout(host)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(slider, stretch=1)
        row.addWidget(value_label)
        return host

    def append_log(self, message: str) -> None:
        self.log_output.appendPlainText(message)

    def _apply_config_to_ui(self) -> None:
        self.camera_name_edit.setText(self.cfg.get("selected_camera_id", "") or "Camera 1")
        self.wifi_ssid_edit.setText(self.cfg.get("wifi_ssid", ""))
        self.wifi_password_edit.setText(self.cfg.get("wifi_password", ""))
        self.stream_url_edit.setText(self.cfg.get("stream_url", ""))
        self.camera_base_url_edit.setText(self.cfg.get("camera_base_url", ""))
        self.resolution_combo.setCurrentText(self.cfg.get("resolution", "VGA"))
        self.auto_apply_check.setChecked(bool(self.cfg.get("auto_apply_camera_controls", False)))
        for spec in CAMERA_CONTROL_SPECS:
            widget = self.camera_control_widgets[spec.key]
            value = self.cfg.get(spec.key, spec.default)
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            else:
                widget.setValue(int(value))
        self.detection_enabled_check.setChecked(bool(self.cfg.get("detection_enabled", False)))
        self.device_combo.setCurrentText(self.cfg.get("device", "auto").capitalize())
        self.img_size_spin.setValue(int(self.cfg.get("img_size", 640)))
    def _selected_model_name(self) -> str:
        return display_to_model_name(self.model_combo.currentText().strip())

    def _read_ui_into_config(self) -> None:
        self.cfg["wifi_ssid"] = self.wifi_ssid_edit.text().strip()
        self.cfg["wifi_password"] = self.wifi_password_edit.text().strip()
        self.cfg["stream_url"] = self.stream_url_edit.text().strip()
        self.cfg["camera_base_url"] = self.camera_base_url_edit.text().strip()
        self.cfg["resolution"] = self.resolution_combo.currentText()
        self.cfg["auto_apply_camera_controls"] = bool(self.auto_apply_check.isChecked())
        for spec in CAMERA_CONTROL_SPECS:
            widget = self.camera_control_widgets[spec.key]
            self.cfg[spec.key] = bool(widget.isChecked()) if isinstance(widget, QCheckBox) else int(widget.value())
        self.cfg["detection_enabled"] = bool(self.detection_enabled_check.isChecked())
        self.cfg["device"] = self.device_combo.currentText().lower()
        self.cfg["confidence"] = round(self.confidence_slider.value() / 100.0, 2)
        self.cfg["iou"] = round(self.iou_slider.value() / 100.0, 2)
        self.cfg["img_size"] = int(self.img_size_spin.value())
        self.cfg["preferred_model"] = self._selected_model_name()
        self.cfg["model_path"] = resolve_model_path(self.cfg["preferred_model"])

        enabled_classes = []
        for class_name, checkbox in self.class_checks.items():
            if checkbox.isChecked():
                enabled_classes.append(class_name)
        if self.class_checks and len(enabled_classes) == len(self.class_checks):
            enabled_classes = []
        self.cfg["enabled_classes"] = enabled_classes

    def _refresh_setup_banner(self) -> None:
        camera = active_camera(self.cfg)
        if camera is None:
            self.setup_banner.setText("No paired camera found. Connect an ESP32-CAM over USB, enter Wi-Fi credentials, and click Pair Camera.")
        else:
            self.setup_banner.setText(f"Active camera: {camera.get('name')} ({camera.get('board_label')}). Runtime preview uses Wi-Fi at {camera.get('stream_url')}.")

    def refresh_serial_ports(self) -> None:
        current_device = self.port_combo.currentData()
        self.port_combo.clear()
        candidates = list_serial_candidates()
        for candidate in candidates:
            label = f"{candidate.device} | {candidate.description}"
            self.port_combo.addItem(label, candidate)
        if not candidates:
            self.port_combo.addItem("No serial devices detected", None)
            self.detected_board_label.setText("No serial device selected.")
            return
        if current_device:
            for index in range(self.port_combo.count()):
                candidate = self.port_combo.itemData(index)
                if candidate and candidate.device == current_device:
                    self.port_combo.setCurrentIndex(index)
                    break
        self.on_port_selection_changed()

    def on_port_selection_changed(self) -> None:
        candidate = self.port_combo.currentData()
        if candidate is None:
            self.detected_board_label.setText("No serial device selected.")
            return
        package_ok, package_message = firmware_package_status(candidate.board_key)
        support_line = "Bundled firmware package ready." if package_ok else package_message
        self.detected_board_label.setText(
            f"It looks like you're using a {candidate.board_label}. {candidate.detection_note} {support_line}"
        )
        for index in range(self.board_override_combo.count()):
            if self.board_override_combo.itemData(index) == candidate.board_key:
                self.board_override_combo.setCurrentIndex(index)
                break
        if not self.camera_name_edit.text().strip():
            self.camera_name_edit.setText(candidate.board_label)

    def refresh_paired_cameras(self) -> None:
        selected_id = self.cfg.get("selected_camera_id", "")
        self.paired_camera_combo.blockSignals(True)
        self.paired_camera_combo.clear()
        for camera in self.cfg.get("paired_cameras", []):
            self.paired_camera_combo.addItem(camera.get("name", camera.get("id", "Camera")), camera.get("id"))
        self.paired_camera_combo.blockSignals(False)
        if self.paired_camera_combo.count() == 0:
            self.active_camera_label.setText("No paired camera selected.")
            self._refresh_setup_banner()
            return
        index_to_select = 0
        for index in range(self.paired_camera_combo.count()):
            if self.paired_camera_combo.itemData(index) == selected_id:
                index_to_select = index
                break
        self.paired_camera_combo.setCurrentIndex(index_to_select)
        self.on_paired_camera_changed()

    def on_paired_camera_changed(self) -> None:
        camera_id = self.paired_camera_combo.currentData()
        if not camera_id:
            self.active_camera_label.setText("No paired camera selected.")
            return
        self.cfg["selected_camera_id"] = camera_id
        camera = active_camera(self.cfg)
        if camera is None:
            return
        self.stream_url_edit.setText(camera.get("stream_url", ""))
        self.camera_base_url_edit.setText(camera.get("camera_base_url", ""))
        self.cfg["stream_url"] = camera.get("stream_url", "")
        self.cfg["camera_base_url"] = camera.get("camera_base_url", "")
        self.active_camera_label.setText(f"{camera.get('name')} on {camera.get('stream_url')}")
        self._refresh_setup_banner()

    def start_pairing(self) -> None:
        candidate = self.port_combo.currentData()
        if candidate is None:
            QMessageBox.warning(self, "Pair Camera", "No serial device selected.")
            return
        camera_name = self.camera_name_edit.text().strip()
        wifi_ssid = self.wifi_ssid_edit.text().strip()
        wifi_password = self.wifi_password_edit.text().strip()
        if not camera_name or not wifi_ssid or not wifi_password:
            QMessageBox.warning(self, "Pair Camera", "Camera name, Wi-Fi SSID, and Wi-Fi password are required.")
            return

        board_profile = profile_by_key(self.board_override_combo.currentData() or candidate.board_key)
        self._read_ui_into_config()
        self.cfg["wifi_ssid"] = wifi_ssid
        self.cfg["wifi_password"] = wifi_password
        save_config(self.cfg)

        self.pair_button.setEnabled(False)
        self.pairing_status_label.setText("Pairing in progress. If upload stalls, press RST on the camera once.")
        self.append_log(f"Starting pairing for {camera_name} on {candidate.device} using {board_profile.label}.")

        self.pair_worker = PairingWorker(candidate.device, board_profile.key, camera_name, wifi_ssid, wifi_password)
        self.pair_worker.log_message.connect(self.append_log)
        self.pair_worker.pairing_finished.connect(self.on_pairing_finished)
        self.pair_worker.start()
    def on_pairing_finished(self, result: dict) -> None:
        self.pair_button.setEnabled(True)
        self.pairing_status_label.setText(result.get("message", "Pairing complete."))
        details = result.get("details", "")
        if result.get("ok"):
            camera = result["camera"]
            paired = [entry for entry in self.cfg.get("paired_cameras", []) if entry.get("id") != camera.get("id")]
            paired.append(camera)
            self.cfg["paired_cameras"] = paired
            self.cfg["selected_camera_id"] = camera["id"]
            self.cfg["stream_url"] = camera["stream_url"]
            self.cfg["camera_base_url"] = camera["camera_base_url"]
            save_config(self.cfg)
            self.refresh_paired_cameras()
            self.stream_url_edit.setText(camera["stream_url"])
            self.camera_base_url_edit.setText(camera["camera_base_url"])
            QMessageBox.information(self, "Pairing Successful", f"{result['message']}\n\n{details}")
        else:
            fixes = result.get("fixes", [])
            fix_text = "\n".join(f"- {item}" for item in fixes)
            message = f"{result.get('message', 'Pairing failed.')}\n\n{details}"
            if fix_text:
                message += f"\n\nPossible fixes:\n{fix_text}"
            QMessageBox.warning(self, "Pairing Failed", message)

    def refresh_models(self) -> None:
        current = self.cfg.get("preferred_model", DEFAULT_MODEL)
        state = model_install_state()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for label in display_names():
            self.model_combo.addItem(label)
        custom_path = self.cfg.get("model_path", "")
        if custom_path and Path(custom_path).exists() and self.model_combo.findText(custom_path) < 0:
            self.model_combo.addItem(custom_path)
        current_display = None
        if current in RECOMMENDED_MODELS:
            suffix = "Installed" if state.get(current, False) else "Download"
            current_display = f"{current} [{suffix}]"
        elif custom_path:
            current_display = custom_path
        if current_display and self.model_combo.findText(current_display) >= 0:
            self.model_combo.setCurrentText(current_display)
        elif self.model_combo.count() > 0:
            default_suffix = "Installed" if state.get(DEFAULT_MODEL, False) else "Download"
            fallback = f"{DEFAULT_MODEL} [{default_suffix}]"
            index = self.model_combo.findText(fallback)
            self.model_combo.setCurrentIndex(index if index >= 0 else 0)
        self.model_combo.blockSignals(False)
        self._refresh_model_status()

    def choose_model_file(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Select YOLO Model",
            self.cfg.get("model_path", ""),
            "Model Files (*.pt *.onnx);;All Files (*.*)",
        )
        if selected:
            if self.model_combo.findText(selected) < 0:
                self.model_combo.addItem(selected)
            self.model_combo.setCurrentText(selected)
            self._refresh_model_status()

    def _run_model_download(self, models: list[str]) -> bool:
        python_bin = Path(sys.executable)
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "download_models.py"
        command = [str(python_bin), str(script_path), *models]
        self.append_log(f"Downloading model(s): {', '.join(models)}")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.stdout:
            self.append_log(result.stdout.strip())
        if result.stderr:
            self.append_log(result.stderr.strip())
        if result.returncode != 0:
            QMessageBox.warning(self, "Model Download Failed", result.stderr.strip() or result.stdout.strip() or "Unknown error")
            return False
        return True

    def download_selected_model(self) -> None:
        model_name = self._selected_model_name()
        if not model_name or Path(model_name).exists():
            return
        if resolve_model_path(model_name):
            self.refresh_models()
            return
        if self._run_model_download([model_name]):
            self.refresh_models()
            self.model_combo.setCurrentText(f"{model_name} [Installed]")

    def download_all_models(self) -> None:
        missing = [name for name, installed in model_install_state().items() if not installed]
        if not missing:
            QMessageBox.information(self, "Models", "All recommended models are already installed.")
            return
        if self._run_model_download(missing):
            self.refresh_models()

    def _refresh_model_status(self) -> None:
        while self.class_layout.count():
            item = self.class_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.class_checks.clear()

        selected = self._selected_model_name()
        resolved = resolve_model_path(selected) or find_model_path(selected)
        if selected in RECOMMENDED_MODELS and not resolved:
            self.model_status_label.setText(f"{selected} is not installed yet. Use Download Selected Model to prepare it.")
            return
        status = self.detector_probe.inspect_model(resolved or selected, self.device_combo.currentText().lower())
        self.model_status_label.setText(status.message)
        if not status.available:
            return

        saved_enabled = set(self.cfg.get("enabled_classes", []))
        allow_all = len(saved_enabled) == 0
        for class_name in status.classes:
            checkbox = QCheckBox(class_name)
            checkbox.setChecked(allow_all or class_name in saved_enabled)
            self.class_checks[class_name] = checkbox
            self.class_layout.addWidget(checkbox)

    def save_current_config(self) -> None:
        self._read_ui_into_config()
        camera = active_camera(self.cfg)
        if camera is not None:
            camera["stream_url"] = self.cfg["stream_url"]
            camera["camera_base_url"] = self.cfg["camera_base_url"]
        path = save_config(self.cfg)
        self.append_log(f"Saved configuration to {path}")
        if self.cfg.get("auto_apply_camera_controls"):
            self.apply_camera_settings_now()

    def apply_camera_settings_now(self) -> None:
        self._read_ui_into_config()
        save_config(self.cfg)
        try:
            apply_camera_settings(self.cfg)
            self.append_log("Applied camera settings using the ESP32 /control API.")
        except Exception as exc:
            self.append_log(f"Camera control failed: {exc}")
            QMessageBox.warning(self, "Camera Control Failed", str(exc))

    def restore_camera_defaults(self) -> None:
        self.resolution_combo.setCurrentText("VGA")
        for spec in CAMERA_CONTROL_SPECS:
            widget = self.camera_control_widgets[spec.key]
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(spec.default))
            else:
                widget.setValue(int(spec.default))
        self.auto_apply_check.setChecked(False)
        self.append_log("Restored camera controls to app defaults.")

    def start_preview(self) -> None:
        self.save_current_config()
        if self.worker is not None and self.worker.isRunning():
            self.append_log("Preview is already running.")
            return

        if self.cfg.get("detection_enabled") and not resolve_model_path(self.cfg.get("preferred_model", "")) and not Path(self.cfg.get("preferred_model", "")).exists():
            QMessageBox.warning(self, "Detection Model Missing", "The selected YOLO model is not installed yet. Download it first or disable detection.")
            return

        self.worker = StreamWorker(self.cfg)
        self.worker.frame_ready.connect(self.on_frame_ready)
        self.worker.status_changed.connect(self.on_status_changed)
        self.worker.stats_ready.connect(self.on_stats_ready)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.connection_status.setText("Starting preview...")
        self.append_log("Started preview worker.")

    def stop_preview(self) -> None:
        if self.worker is None:
            return
        self.worker.stop()
        self.worker.wait(2000)
        self.worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.connection_status.setText("Preview stopped.")
        self.preview_label.clear()
        self.preview_label.setText("Preview is stopped.")
        self.append_log("Stopped preview worker.")

    def on_frame_ready(self, image) -> None:
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def on_status_changed(self, message: str) -> None:
        self.connection_status.setText(message)

    def on_stats_ready(self, stats: dict) -> None:
        self.stats_label.setText(f"FPS: {stats['fps']} | Detections: {stats['detections']}")

    def on_worker_finished(self) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.connection_status.setText("Preview stopped.")

    def closeEvent(self, event) -> None:
        self.stop_preview()
        if self.pair_worker is not None and self.pair_worker.isRunning():
            self.pair_worker.wait(1000)
        self.save_current_config()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AetherConsoleWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
