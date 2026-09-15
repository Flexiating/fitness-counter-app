"""Pure finite-state push-up counter; it has no MediaPipe or camera dependency."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class PushUpState(str, Enum):
    WAITING = "WAITING"
    READY = "READY"
    UP = "UP"
    DOWN = "DOWN"


@dataclass(frozen=True)
class PushUpResult:
    repetitions: int
    state: PushUpState
    posture: str
    reason: str
    last_transition: str
    form_score: float = 0.0


class PushUpCounter:
    """Count stable, complete READY -> UP -> DOWN -> UP movements.

    The adapter supplies smoothed, best-side measurements under the generic
    ``Selected ...`` keys. Bilateral keys remain supported so this counter is
    easy to exercise independently and compatible with older callers.
    """

    _VISIBILITY_KEYS = (
        "selected_shoulder", "selected_elbow", "selected_wrist",
        "selected_hip", "selected_knee", "selected_ankle",
    )

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
        self._candidate: PushUpState | None = None
        self._candidate_since: float | None = None
        self._invalid_since: float | None = None

    def update(self, angles: Mapping[str, float], visibility: Mapping[str, float], timestamp: float) -> PushUpResult:
        valid, reason = self._valid_posture(angles, visibility)
        form_score = max(0.0, min(100.0, angles.get("Form score", 0.0 if not valid else 75.0)))
        if not valid:
            self._candidate = None
            self._candidate_since = None
            if self._invalid_since is None:
                self._invalid_since = timestamp
            elif timestamp - self._invalid_since >= .75 and self.state is not PushUpState.WAITING:
                self._transition(PushUpState.WAITING, timestamp)
            return PushUpResult(self.repetitions, self.state, "BAD", reason, self.last_transition, form_score)

        self._invalid_since = None
        if self.state is PushUpState.WAITING:
            self._transition(PushUpState.READY, timestamp)

        elbow = self._selected_angle(angles, "elbow")
        # The configured values remain the ideal targets. Small biomechanical
        # tolerance prevents a valid 150-degree top or 90-degree bottom from
        # being mistaken for an incomplete repetition.
        up_entry = max(150.0, self.elbow_up - 10.0)
        down_entry = min(95.0, self.elbow_down + 25.0)
        desired = PushUpState.UP if elbow >= up_entry else (PushUpState.DOWN if elbow <= down_entry else None)
        if desired is None:
            self._candidate = None
            self._candidate_since = None
            return PushUpResult(
                self.repetitions, self.state, "GOOD", "Movement between thresholds",
                self.last_transition, form_score,
            )

        if desired is not self.state and self._confirmed(desired, timestamp):
            previous = self.state
            self._transition(desired, timestamp)
            if previous is PushUpState.DOWN and desired is PushUpState.UP:
                self.repetitions += 1

        posture = "GOOD" if form_score >= 65.0 else "ACCEPTABLE"
        return PushUpResult(self.repetitions, self.state, posture, "", self.last_transition, form_score)

    def _confirmed(self, desired: PushUpState, timestamp: float) -> bool:
        if self._candidate is not desired:
            self._candidate = desired
            self._candidate_since = timestamp
            return False
        if self._candidate_since is None or timestamp - self._candidate_since < self.debounce_seconds:
            return False
        return self._can_transition(timestamp)

    def _transition(self, desired: PushUpState, timestamp: float) -> None:
        previous = self.state
        self.state = desired
        self._last_transition_at = timestamp
        self.last_transition = f"{previous.value} → {desired.value}"
        self._candidate = None
        self._candidate_since = None

    def _can_transition(self, timestamp: float) -> bool:
        return self._last_transition_at is None or timestamp - self._last_transition_at >= self.debounce_seconds

    @staticmethod
    def _selected_angle(angles: Mapping[str, float], joint: str) -> float:
        selected = angles.get(f"Selected {joint}")
        if selected is not None:
            return selected
        values = [angles[name] for name in (f"Left {joint}", f"Right {joint}") if name in angles]
        return min(values) if values else 0.0

    def _valid_posture(self, angles: Mapping[str, float], visibility: Mapping[str, float]) -> tuple[bool, str]:
        elbow = self._selected_angle(angles, "elbow")
        hip = self._selected_angle(angles, "hip")
        if elbow <= 0.0 or hip <= 0.0 or "Body orientation" not in angles:
            return False, "No complete arm and body side detected"

        selected_visibility = [visibility.get(name, -1.0) for name in self._VISIBILITY_KEYS]
        if all(value >= 0.0 for value in selected_visibility):
            average_visibility = sum(selected_visibility) / len(selected_visibility)
            weakest_visibility = min(selected_visibility)
            if average_visibility < .45:
                return False, f"Selected-side visibility {average_visibility:.2f} < 0.45"
            if weakest_visibility < .25:
                weak_index = selected_visibility.index(weakest_visibility)
                joint = self._VISIBILITY_KEYS[weak_index].removeprefix("selected_")
                return False, f"{joint.title()} visibility {weakest_visibility:.2f} < 0.25"
        else:
            # Compatibility path for direct counter clients: accept the most
            # visible complete side instead of requiring both arms.
            side_scores = []
            for side in ("left", "right"):
                names = tuple(f"{side}_{joint}" for joint in ("shoulder", "elbow", "wrist", "hip"))
                if all(name in visibility for name in names):
                    side_scores.append(sum(visibility[name] for name in names) / len(names))
            if not side_scores or max(side_scores) < .45:
                return False, "No sufficiently visible arm and body side"

        if angles.get("Whole body inside", 1.0) < .5:
            return False, "Whole body is not inside the frame"
        body_size = angles.get("Body size")
        if body_size is not None and body_size < .30:
            return False, f"Body occupies only {body_size:.0%} of frame"
        if body_size is not None and body_size > .98:
            return False, f"Body occupies {body_size:.0%} of frame; move slightly farther away"

        orientation_limit = self.plank_max_orientation + 12.0
        if angles["Body orientation"] > orientation_limit:
            return False, "Not in plank position (standing or walking)"

        # Hip and back alignment are graded by the form score. Only clearly
        # folded posture is rejected, allowing natural anatomy and camera angle.
        hard_alignment_floor = max(135.0, 180.0 - self.hip_tolerance - 20.0)
        if hip < hard_alignment_floor or angles.get("Back alignment", hip) < hard_alignment_floor:
            return False, "Hips too high or too low"
        if angles.get("Form score", 100.0) < 50.0:
            return False, "Posture score below safe push-up range"
        return True, ""
