from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from pathlib import Path
from typing import Mapping

from app.exercise.base_counter import BaseCounter, CounterState


@dataclass(frozen=True)
class CrunchResult:
    count: int
    state: CounterState
    posture_valid: bool
    feedback: str
    debug_info: str


def _config() -> dict[str, float]:
    path = Path(__file__).parents[1] / "config" / "crunch.yaml"
    return {key.strip(): float(value.strip()) for line in path.read_text().splitlines() if ":" in line
            for key, value in [line.split(":", 1)]}


class CrunchCounter(BaseCounter):
    """Angle/coordinate-based crunch FSM with visibility and timing safeguards."""
    def __init__(self) -> None:
        cfg = _config(); self.cfg = cfg
        super().__init__(cfg["debounce_ms"] / 1000, cfg["min_rep_time"])

    def update(self, angles: Mapping[str, float], coordinates: Mapping[str, tuple[float, float]], visibility: Mapping[str, float], timestamp: float) -> CrunchResult:
        valid, reason = self._valid(angles, coordinates, visibility)
        if not valid:
            return self._result(False, reason)
        hip = (angles["Left hip"] + angles["Right hip"]) / 2
        target = CounterState.UP if hip >= self.cfg["start_angle"] else (CounterState.DOWN if hip <= self.cfg["finish_angle"] else None)
        if target and target is not self.state and self.can_transition(timestamp):
            previous, self.state, self.last_transition_at = self.state, target, timestamp
            if target is CounterState.DOWN: self.down_at = timestamp
            if previous is CounterState.DOWN and target is CounterState.UP and self.down_at and timestamp - self.down_at >= self.min_rep_seconds:
                self.count += 1
            elif previous is CounterState.DOWN and target is CounterState.UP:
                return self._result(True, "Rep rejected: too fast")
        return self._result(True, "OK" if target else "Partial crunch ignored")

    def _valid(self, angles, coords, visibility) -> tuple[bool, str]:
        required = ("Left hip", "Right hip")
        points = ("nose", "left_shoulder", "left_hip", "left_knee")
        if any(key not in angles for key in required) or any(key not in coords or visibility.get(key, 0) < self.cfg["visibility_threshold"] for key in points):
            return False, "Body not visible or tracking lost"
        shoulder, hip = coords["left_shoulder"], coords["left_hip"]
        if abs(hip[1] - shoulder[1]) > abs(hip[0] - shoulder[0]):
            return False, "Standing, sitting, walking, or body rotated"
        return True, ""

    def _result(self, valid: bool, feedback: str) -> CrunchResult:
        debug = f"state={self.state.value}; thresholds={self.cfg['start_angle']:.0f}/{self.cfg['finish_angle']:.0f}; {feedback}"
        return CrunchResult(self.count, self.state, valid, feedback, debug)
