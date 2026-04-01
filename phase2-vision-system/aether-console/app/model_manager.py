"""
YOLO model inventory helper.

Current product decision:
- Install only yolov8n by default so first-time setup is faster.
- Offer yolov8s/m/l/x as on-demand downloads from the app.
- Keep downloaded models cached locally for future sessions.

Why:
- Compressing/uncompressing models on every switch would add complexity and switching latency.
- On-demand download is the simpler and more professional UX for this product.
"""
from __future__ import annotations

from pathlib import Path

from config_manager import installed_model_paths, models_dir


DEFAULT_MODEL = "yolov8n.pt"
RECOMMENDED_MODELS = [
    "yolov8n.pt",
    "yolov8s.pt",
    "yolov8m.pt",
    "yolov8l.pt",
    "yolov8x.pt",
]


def installed_models() -> list[Path]:
    return installed_model_paths()


def installed_model_names() -> list[str]:
    return [path.name for path in installed_models()]


def model_install_state() -> dict[str, bool]:
    installed = set(installed_model_names())
    return {name: (name in installed) for name in RECOMMENDED_MODELS}


def display_names() -> list[str]:
    state = model_install_state()
    labels = []
    for name in RECOMMENDED_MODELS:
        suffix = "Installed" if state[name] else "Download"
        labels.append(f"{name} [{suffix}]")
    return labels


def display_to_model_name(display: str) -> str:
    if " [" in display:
        return display.split(" [", 1)[0].strip()
    return display.strip()


def resolve_model_path(name_or_path: str) -> str:
    if not name_or_path:
        return ""
    path = Path(name_or_path)
    if path.exists():
        return str(path)
    model_name = display_to_model_name(name_or_path)
    candidate = models_dir() / model_name
    if candidate.exists():
        return str(candidate)
    return ""

