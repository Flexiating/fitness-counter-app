from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from app.utils.paths import app_data_path


@dataclass
class Settings:
    dark_mode: bool = True
    language: str = "vi"
    camera_index: int = 0
    camera_width: int = 960
    camera_height: int = 540
    target_fps: int = 30
    # Full pose landmarks are materially more reliable for floor exercises
    # where the far-side arm and hip can be partially occluded.
    pose_model_complexity: int = 1
    pose_min_confidence: float = 0.55
    pose_tracking_confidence: float = 0.55
    min_visibility: float = 0.55
    smoothing_window: int = 5
    worker_stack_bytes: int = 8 * 1024 * 1024
    pushup_elbow_down: float = 70.0
    pushup_elbow_up: float = 160.0
    pushup_hip_tolerance: float = 25.0
    pushup_debounce_seconds: float = .2
    pushup_body_orientation_limit: float = 35.0


SETTINGS = Settings()


class SettingsStore:
    """Persist user-editable settings while keeping a shared runtime object."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else app_data_path("settings.json")

    def load(self) -> Settings:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return SETTINGS
        allowed = {item.name for item in fields(Settings)}
        for key, value in raw.items():
            if key in allowed:
                setattr(SETTINGS, key, value)
        if SETTINGS.language not in {"en", "vi"}:
            SETTINGS.language = "en"
        return SETTINGS

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(SETTINGS), indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def update(self, **values: object) -> None:
        allowed = {item.name for item in fields(Settings)}
        for key, value in values.items():
            if key not in allowed:
                raise KeyError(key)
            setattr(SETTINGS, key, value)
        self.save()
