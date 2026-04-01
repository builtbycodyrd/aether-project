from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2

from model_manager import resolve_model_path


@dataclass
class DetectorStatus:
    available: bool
    message: str
    classes: list[str]


class OptionalDetector:
    def __init__(self) -> None:
        self.model = None
        self.model_path: str = ""
        self.device_pref = "auto"
        self.classes: list[str] = []
        self.last_status = DetectorStatus(False, "Detection idle.", [])

    def inspect_model(self, model_path: str, device_pref: str) -> DetectorStatus:
        self.model_path = resolve_model_path(model_path.strip())
        self.device_pref = device_pref

        if not self.model_path:
            self.model = None
            self.classes = []
            self.last_status = DetectorStatus(False, "No model selected or installed.", [])
            return self.last_status

        model_file = Path(self.model_path)
        if not model_file.exists():
            self.model = None
            self.classes = []
            self.last_status = DetectorStatus(False, f"Model not found: {model_file}", [])
            return self.last_status

        try:
            from ultralytics import YOLO
        except Exception as exc:
            self.model = None
            self.classes = []
            self.last_status = DetectorStatus(False, f"Ultralytics is unavailable: {exc}", [])
            return self.last_status

        try:
            model = YOLO(str(model_file))
            self.model = model
            self.classes = [model.names[i] for i in sorted(model.names.keys())]
            self.last_status = DetectorStatus(True, f"Loaded model: {model_file.name}", self.classes[:])
            return self.last_status
        except Exception as exc:
            self.model = None
            self.classes = []
            self.last_status = DetectorStatus(False, f"Failed to load model: {exc}", [])
            return self.last_status

    def _resolve_device(self, device_pref: str):
        if device_pref == "cpu":
            return "cpu"
        try:
            import torch

            if device_pref == "gpu":
                return 0 if torch.cuda.is_available() else "cpu"
            return 0 if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def apply(
        self,
        frame,
        confidence: float,
        iou: float,
        img_size: int,
        enabled_classes: list[str],
        device_pref: str,
    ):
        if self.model is None:
            return frame, 0, "Detection disabled."

        class_ids = None
        if enabled_classes:
            name_to_id = {name: idx for idx, name in self.model.names.items()}
            class_ids = [int(name_to_id[name]) for name in enabled_classes if name in name_to_id]

        device = self._resolve_device(device_pref)
        try:
            results = self.model.predict(
                source=frame,
                conf=confidence,
                iou=iou,
                imgsz=img_size,
                classes=class_ids if class_ids else None,
                device=device,
                verbose=False,
            )
            plotted = results[0].plot()
            boxes = getattr(results[0], "boxes", None)
            count = len(boxes) if boxes is not None else 0
            return plotted, count, f"Detection active on {device_pref.upper() if device_pref != 'auto' else 'AUTO'}"
        except Exception as exc:
            return frame, 0, f"Detection error: {exc}"


def to_qimage(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    from PyQt6.QtGui import QImage

    return QImage(
        rgb.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888,
    ).copy()
