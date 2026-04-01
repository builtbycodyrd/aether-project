from __future__ import annotations

import time

import cv2
from PyQt6.QtCore import QThread, pyqtSignal

# The reference repo separated stream preview and vision work into helper modules.
# This worker keeps that separation, but limits the runtime to camera preview and optional detector overlay.
from detection import OptionalDetector, to_qimage


class StreamWorker(QThread):
    frame_ready = pyqtSignal(object)
    status_changed = pyqtSignal(str)
    stats_ready = pyqtSignal(dict)

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = dict(cfg)
        self._running = True
        self.detector = OptionalDetector()
        self._last_fps_sample = time.perf_counter()
        self._frames_since_sample = 0
        self._fps_value = 0.0

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        stream_url = self.cfg.get("stream_url", "").strip()
        if not stream_url:
            self.status_changed.emit("No stream URL configured. Pair a camera first or enter a stream URL.")
            return

        self.status_changed.emit(f"Opening stream: {stream_url}")
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            self.status_changed.emit(f"Could not open stream: {stream_url}")
            return

        detector_status = self.detector.inspect_model(
            self.cfg.get("model_path") or self.cfg.get("preferred_model", ""),
            self.cfg.get("device", "auto"),
        )
        if self.cfg.get("detection_enabled"):
            self.status_changed.emit(detector_status.message)

        while self._running:
            ok, frame = cap.read()
            if not ok:
                self.msleep(10)
                continue

            detection_count = 0
            detection_message = "Preview active."

            if self.cfg.get("detection_enabled"):
                frame, detection_count, detection_message = self.detector.apply(
                    frame=frame,
                    confidence=float(self.cfg.get("confidence", 0.25)),
                    iou=float(self.cfg.get("iou", 0.45)),
                    img_size=int(self.cfg.get("img_size", 640)),
                    enabled_classes=list(self.cfg.get("enabled_classes", [])),
                    device_pref=self.cfg.get("device", "auto"),
                )

            self._frames_since_sample += 1
            now = time.perf_counter()
            elapsed = now - self._last_fps_sample
            if elapsed >= 1.0:
                self._fps_value = self._frames_since_sample / elapsed
                self._frames_since_sample = 0
                self._last_fps_sample = now

            self.frame_ready.emit(to_qimage(frame))
            self.status_changed.emit(detection_message)
            self.stats_ready.emit({"fps": round(self._fps_value, 1), "detections": detection_count})
            self.msleep(10)

        cap.release()
        self.status_changed.emit("Stream stopped.")
