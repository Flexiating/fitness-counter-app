"""Pure finite-state push-up counter; it has no MediaPipe or camera dependency."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class PushUpState(str, Enum):
    WAITING = "WAITING"
    UP = "UP"
    DOWN = "DOWN"


@dataclass(frozen=True)
class PushUpResult:
    repetitions: int
    state: PushUpState
    posture: str
    reason: str
    last_transition: str


class PushUpCounter:
    """Counts only stable, complete UP → DOWN → UP movements."""

    def __init__(self, elbow_down: float = 70.0, elbow_up: float = 160.0,
                 hip_tolerance: float = 25.0, debounce_seconds: float = .2,
                 plank_max_orientation: float = 35.0) -> None:
        self.elbow_down, self.elbow_up = elbow_down, elbow_up
        self.hip_tolerance, self.debounce_seconds = hip_tolerance, debounce_seconds
        self.plank_max_orientation = plank_max_orientation
        self.reset()

    def reset(self) -> None:
        self.repetitions = 0
        self.state = PushUpState.WAITING
        self.last_transition = "None"
        self._last_transition_at: float | None = None

    def update(self, angles: Mapping[str, float], visibility: Mapping[str, float], timestamp: float) -> PushUpResult:
        valid, reason = self._valid_posture(angles, visibility)
        if not valid:
            return PushUpResult(self.repetitions, self.state, "BAD", reason, self.last_transition)
        elbow = min(angles["Left elbow"], angles["Right elbow"])
        desired = PushUpState.UP if elbow >= self.elbow_up else (PushUpState.DOWN if elbow <= self.elbow_down else None)
        if desired is None:
            return PushUpResult(self.repetitions, self.state, "GOOD", "Movement between thresholds", self.last_transition)
        if desired is not self.state and self._can_transition(timestamp):
            previous, self.state = self.state, desired
            self._last_transition_at = timestamp
            self.last_transition = f"{previous.value} → {desired.value}"
            if previous is PushUpState.DOWN and desired is PushUpState.UP:
                self.repetitions += 1
        return PushUpResult(self.repetitions, self.state, "GOOD", "", self.last_transition)

    def _can_transition(self, timestamp: float) -> bool:
        return self._last_transition_at is None or timestamp - self._last_transition_at >= self.debounce_seconds

    def _valid_posture(self, angles: Mapping[str, float], visibility: Mapping[str, float]) -> tuple[bool, str]:
        required = ("Left elbow", "Right elbow", "Left hip", "Right hip", "Body orientation")
        if any(name not in angles for name in required):
            return False, "Only one arm detected or body not visible"
        if any(visibility.get(name, 0.0) < .55 for name in ("left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip")):
            return False, "Body not visible"
        if angles["Body orientation"] > self.plank_max_orientation:
            return False, "Not in plank position (standing or walking)"
        hip_floor = 180.0 - self.hip_tolerance
        if angles["Left hip"] < hip_floor or angles["Right hip"] < hip_floor:
            return False, "Hips too high or too low"
        return True, ""
