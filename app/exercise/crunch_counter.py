"""Dedicated, MediaPipe-independent crunch state machine and form evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from math import hypot
from typing import Mapping

from app.utils.paths import resource_path


class CrunchState(str, Enum):
    WAITING = "WAITING"
    READY = "READY"
    DOWN = "DOWN"  # shoulders resting in the extended/lying position
    UP = "UP"      # shoulders lifted in the contracted crunch position


@dataclass(frozen=True)
class CrunchResult:
    count: int
    state: CrunchState
    posture_valid: bool
    feedback: str
    debug_info: str
    form_score: float = 0.0


@lru_cache(maxsize=1)
def _config() -> dict[str, float]:
    path = resource_path("app", "config", "crunch.yaml")
    return {
        key.strip(): float(value.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if ":" in line
        for key, value in [line.split(":", 1)]
    }


class CrunchCounter:
    """Count a crunch only after a stable lying -> lifted -> lying cycle."""

    _VISIBILITY_KEYS = (
        "selected_head",
        "selected_shoulder",
        "selected_hip",
        "selected_knee",
        "selected_ankle",
    )

    def __init__(self) -> None:
        self.cfg = dict(_config())
        self.debounce_seconds = self.cfg["debounce_ms"] / 1000.0
        self.min_rep_seconds = self.cfg["min_rep_time"]
        self.reset()

    def reset(self) -> None:
        self.count = 0
        self.state = CrunchState.WAITING
        self.last_transition = "None"
        self.last_transition_at: float | None = None
        self.last_accepted_rep: float | None = None
        self.last_rejected_rep = "None"
        self._candidate: CrunchState | None = None
        self._candidate_since: float | None = None
        self._invalid_since: float | None = None
        self._cycle_started_at: float | None = None
        self._cycle_max_angle: float | None = None
        self._cycle_min_angle: float | None = None
        self._baseline_hip: tuple[float, float] | None = None
        self._previous_angle: float | None = None
        self._previous_speed = 0.0
        self._previous_timestamp: float | None = None
        self._score_ema: float | None = None

    def update(
        self,
        angles: Mapping[str, float],
        coordinates: Mapping[str, tuple[float, float]],
        visibility: Mapping[str, float],
        timestamp: float,
    ) -> CrunchResult:
        valid, rejection = self._valid(angles, coordinates, visibility)
        if not valid:
            self._candidate = None
            self._candidate_since = None
            if self._invalid_since is None:
                self._invalid_since = timestamp
            elif timestamp - self._invalid_since >= .75 and self.state is not CrunchState.WAITING:
                self._transition(CrunchState.WAITING, timestamp)
                self._clear_cycle()
            self.last_rejected_rep = rejection
            return self._result(False, rejection, angles, 0.0)

        self._invalid_since = None
        speed, smoothness = self._motion_quality(angles["Hip angle"], timestamp)
        hip_shift = self._hip_shift(coordinates)
        lying = self._is_lying(angles)
        lifted = self._is_lifted(angles)
        self._track_range(angles["Hip angle"])

        if self.state is CrunchState.WAITING:
            self._transition(CrunchState.READY, timestamp)

        completed = False
        feedback = self._feedback(angles, lying, lifted, speed, hip_shift)
        target: CrunchState | None = None
        if self.state is CrunchState.READY and lying:
            target = CrunchState.DOWN
        elif self.state is CrunchState.DOWN and lifted:
            target = CrunchState.UP
        elif self.state is CrunchState.UP and lying:
            target = CrunchState.DOWN

        if target is None:
            self._candidate = None
            self._candidate_since = None
        elif self._confirmed(target, timestamp):
            previous = self.state
            self._transition(target, timestamp)
            if previous is CrunchState.READY and target is CrunchState.DOWN:
                self._start_cycle(timestamp, angles["Hip angle"], coordinates)
                feedback = "Lift your shoulders higher."
            elif previous is CrunchState.DOWN and target is CrunchState.UP:
                feedback = "Good lift. Lower your shoulders with control."
            elif previous is CrunchState.UP and target is CrunchState.DOWN:
                completed, feedback = self._complete_cycle(timestamp, angles, speed)
                if completed:
                    self.count += 1
                    self.last_accepted_rep = timestamp
                    self.last_rejected_rep = "None"
                    feedback = "Good crunch."
                self._start_cycle(timestamp, angles["Hip angle"], coordinates)

        score = self._form_score(angles, lying, lifted, speed, smoothness, hip_shift)
        self._score_ema = score if self._score_ema is None else .22 * score + .78 * self._score_ema
        return self._result(True, feedback, angles, self._score_ema)

    def _valid(
        self,
        angles: Mapping[str, float],
        coordinates: Mapping[str, tuple[float, float]],
        visibility: Mapping[str, float],
    ) -> tuple[bool, str]:
        required_angles = (
            "Hip angle",
            "Torso angle",
            "Shoulder lift",
            "Lower body angle",
            "Body rotation",
            "Body size",
            "Whole body inside",
            "Neck angle",
            "Shoulder-hip ratio",
            "Nose-knee ratio",
        )
        if any(name not in angles for name in required_angles) or "selected_hip" not in coordinates:
            return False, "Body not visible or tracking lost"

        values = [visibility.get(name, 0.0) for name in self._VISIBILITY_KEYS]
        average = sum(values) / len(values)
        weakest = min(values)
        if average < self.cfg["visibility_threshold"]:
            return False, f"Selected-side visibility {average:.2f} below threshold"
        if weakest < .20:
            joint = self._VISIBILITY_KEYS[values.index(weakest)].removeprefix("selected_")
            return False, f"{joint.title()} visibility {weakest:.2f} below threshold"
        if angles["Whole body inside"] < .5:
            return False, "Keep your full body inside the frame"
        if angles["Body size"] < self.cfg["min_body_size"]:
            return False, f"Body occupies only {angles['Body size']:.0%} of frame"
        if angles["Body size"] > self.cfg["max_body_size"]:
            return False, "Move slightly farther from the camera"
        if angles["Body rotation"] > self.cfg["body_rotation_limit"]:
            return False, "Turn sideways to the camera"
        if angles["Lower body angle"] > self.cfg["max_lower_body_angle"]:
            return False, "Standing, sitting, or walking is not a crunch position"
        if angles["Torso angle"] > self.cfg["max_torso_angle"]:
            return False, "Standing or sitting is not a crunch position"
        return True, ""

    def _is_lying(self, angles: Mapping[str, float]) -> bool:
        votes = (
            angles["Hip angle"] >= self.cfg["start_angle"] - 20.0,
            angles["Torso angle"] <= self.cfg["lying_torso_angle"],
            angles["Shoulder lift"] <= self.cfg["lying_shoulder_lift"],
            angles["Shoulder-hip ratio"] >= .88,
        )
        return sum(votes) >= 3

    def _is_lifted(self, angles: Mapping[str, float]) -> bool:
        hip_flexed = angles["Hip angle"] <= self.cfg["finish_angle"] + 5.0
        torso_lifted = angles["Torso angle"] >= self.cfg["lift_torso_angle"]
        votes = (
            hip_flexed,
            torso_lifted,
            angles["Shoulder lift"] >= self.cfg["lift_shoulder_ratio"],
            angles["Shoulder-hip ratio"] <= .90,
            angles["Nose-knee ratio"] <= .94,
        )
        return sum(votes) >= 3 and (hip_flexed or torso_lifted)

    def _confirmed(self, target: CrunchState, timestamp: float) -> bool:
        if self._candidate is not target:
            self._candidate = target
            self._candidate_since = timestamp
            return False
        if self._candidate_since is None or timestamp - self._candidate_since < self.debounce_seconds:
            return False
        return self.last_transition_at is None or timestamp - self.last_transition_at >= self.debounce_seconds

    def _transition(self, target: CrunchState, timestamp: float) -> None:
        previous = self.state
        self.state = target
        self.last_transition_at = timestamp
        self.last_transition = f"{previous.value} → {target.value}"
        self._candidate = None
        self._candidate_since = None

    def _start_cycle(
        self,
        timestamp: float,
        hip_angle: float,
        coordinates: Mapping[str, tuple[float, float]],
    ) -> None:
        self._cycle_started_at = timestamp
        self._cycle_max_angle = hip_angle
        self._cycle_min_angle = hip_angle
        self._baseline_hip = coordinates.get("selected_hip")

    def _track_range(self, hip_angle: float) -> None:
        if self._cycle_started_at is None:
            return
        self._cycle_max_angle = hip_angle if self._cycle_max_angle is None else max(self._cycle_max_angle, hip_angle)
        self._cycle_min_angle = hip_angle if self._cycle_min_angle is None else min(self._cycle_min_angle, hip_angle)

    def _complete_cycle(
        self,
        timestamp: float,
        angles: Mapping[str, float],
        speed: float,
    ) -> tuple[bool, str]:
        duration = timestamp - self._cycle_started_at if self._cycle_started_at is not None else 0.0
        observed_range = (
            (self._cycle_max_angle or angles["Hip angle"])
            - (self._cycle_min_angle or angles["Hip angle"])
        )
        minimum_range = (self.cfg["start_angle"] - self.cfg["finish_angle"]) * .65
        if duration < self.min_rep_seconds:
            self.last_rejected_rep = f"Too fast ({duration:.2f}s)"
            return False, "Move more slowly."
        if observed_range < minimum_range:
            self.last_rejected_rep = f"Partial range ({observed_range:.0f}°)"
            return False, "Complete the full range of motion."
        if speed > self.cfg["max_angular_speed"]:
            self.last_rejected_rep = f"Uncontrolled speed ({speed:.0f}°/s)"
            return False, "Move more slowly."
        return True, "Good crunch."

    def _clear_cycle(self) -> None:
        self._cycle_started_at = None
        self._cycle_max_angle = None
        self._cycle_min_angle = None
        self._baseline_hip = None

    def _hip_shift(self, coordinates: Mapping[str, tuple[float, float]]) -> float:
        current = coordinates.get("selected_hip")
        if current is None or self._baseline_hip is None:
            return 0.0
        return hypot(current[0] - self._baseline_hip[0], current[1] - self._baseline_hip[1])

    def _motion_quality(self, hip_angle: float, timestamp: float) -> tuple[float, float]:
        if self._previous_angle is None or self._previous_timestamp is None:
            speed = 0.0
            smoothness = 100.0
        else:
            elapsed = max(.001, timestamp - self._previous_timestamp)
            speed = abs(hip_angle - self._previous_angle) / elapsed
            acceleration = abs(speed - self._previous_speed)
            smoothness = max(0.0, 100.0 - acceleration * .30)
        self._previous_angle = hip_angle
        self._previous_speed = speed
        self._previous_timestamp = timestamp
        return speed, smoothness

    def _form_score(
        self,
        angles: Mapping[str, float],
        lying: bool,
        lifted: bool,
        speed: float,
        smoothness: float,
        hip_shift: float,
    ) -> float:
        expected_range = max(1.0, self.cfg["start_angle"] - self.cfg["finish_angle"])
        flexion_progress = (self.cfg["start_angle"] - angles["Hip angle"]) / expected_range
        lift_progress = max(flexion_progress, angles["Shoulder lift"])
        lift_score = 100.0 if lifted else 90.0 if lying else max(45.0, min(95.0, lift_progress * 100.0))
        neck_score = self._straight_score(angles["Neck angle"])
        lower_back_score = max(0.0, 100.0 * (1.0 - hip_shift / self.cfg["max_hip_shift"]))
        control_score = 100.0 if speed <= 180.0 else max(0.0, 100.0 - (speed - 180.0) * .55)
        if self._cycle_max_angle is None or self._cycle_min_angle is None:
            range_score = 85.0
        else:
            observed = self._cycle_max_angle - self._cycle_min_angle
            range_score = max(55.0, min(100.0, observed / expected_range * 100.0))
        return (
            .30 * lift_score
            + .15 * control_score
            + .15 * neck_score
            + .20 * lower_back_score
            + .10 * smoothness
            + .10 * range_score
        )

    @staticmethod
    def _straight_score(angle: float) -> float:
        if angle >= 165.0:
            return 100.0
        if angle >= 150.0:
            return 75.0 + (angle - 150.0) * (25.0 / 15.0)
        if angle >= 135.0:
            return 50.0 + (angle - 135.0) * (25.0 / 15.0)
        return max(0.0, angle - 85.0)

    def _feedback(
        self,
        angles: Mapping[str, float],
        lying: bool,
        lifted: bool,
        speed: float,
        hip_shift: float,
    ) -> str:
        if angles["Neck angle"] < self.cfg["min_neck_angle"]:
            return "Avoid pulling your neck."
        if hip_shift > self.cfg["max_hip_shift"]:
            return "Keep your lower back on the floor."
        if speed > self.cfg["max_angular_speed"]:
            return "Move more slowly."
        if self.state is CrunchState.READY and not lying:
            return "Lie back fully before starting."
        if self.state is CrunchState.DOWN and not lifted:
            return "Lift your shoulders higher."
        if self.state is CrunchState.UP and not lying:
            return "Lower your shoulders with control."
        return "Ready for the next crunch." if lying else "Good torso lift."

    def _result(
        self,
        valid: bool,
        feedback: str,
        angles: Mapping[str, float],
        form_score: float,
    ) -> CrunchResult:
        primary = angles.get("Hip angle", 0.0)
        flexion = angles.get("Torso flexion", 0.0)
        torso = angles.get("Torso angle", 0.0)
        debug = (
            "Exercise: Crunch | Loaded detector: CrunchDetector | "
            "State machine: CrunchStateMachine | "
            f"Current state: {self.state.value} | Rep stage: {self.state.value} | "
            f"Primary angles: torso flexion {flexion:.1f}°, hip {primary:.1f}°, "
            f"torso {torso:.1f}° | "
            f"Thresholds: lying ≥{self.cfg['start_angle']:.0f}°, "
            f"lifted ≤{self.cfg['finish_angle']:.0f}° | "
            f"Form score: {form_score:.0f}% | Last transition: {self.last_transition} | "
            f"Last accepted rep: {self.last_accepted_rep if self.last_accepted_rep is not None else 'None'} | "
            f"Last rejected rep: {self.last_rejected_rep} | Reason: {feedback}"
        )
        return CrunchResult(self.count, self.state, valid, feedback, debug, form_score)
