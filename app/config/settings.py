from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    camera_width: int = 960
    camera_height: int = 540
    target_fps: int = 30
    pose_model_complexity: int = 0
    pose_min_confidence: float = 0.55
    pose_tracking_confidence: float = 0.55
    min_visibility: float = 0.55
    smoothing_window: int = 5
    worker_stack_bytes: int = 8 * 1024 * 1024
    pushup_elbow_down: float = 70.0
    pushup_elbow_up: float = 160.0
    pushup_hip_tolerance: float = 25.0
    pushup_debounce_seconds: float = .2
    pushup_plank_max_orientation: float = 35.0


SETTINGS = Settings()
