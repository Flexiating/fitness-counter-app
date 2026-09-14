from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    camera_width: int = 960
    camera_height: int = 540
    target_fps: int = 30
    pose_min_confidence: float = 0.55
    pose_tracking_confidence: float = 0.55
    min_visibility: float = 0.55
    smoothing_window: int = 5
    push_up_up_threshold: float = 155.0
    push_up_down_threshold: float = 95.0
    crunch_extended_threshold: float = 150.0
    crunch_contracted_threshold: float = 115.0
    minimum_state_frames: int = 3
    worker_stack_bytes: int = 8 * 1024 * 1024


SETTINGS = Settings()
