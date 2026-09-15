"""Dedicated crunch detector built on standardized pose landmarks."""

from __future__ import annotations

from math import acos, atan2, degrees, hypot
from time import monotonic

from app.config.settings import SETTINGS
from app.exercise.crunch_counter import CrunchCounter
from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.pose.angles import calculate_joint_angles
from app.pose.pose_landmarks import Landmark, LandmarkName, PoseLandmarks


_CRUNCH_BODY_JOINTS = ("shoulder", "hip", "knee", "ankle")


class CrunchDetector(BaseExercise):
    """Analyze torso motion without using push-up angles or state."""

    name = "Crunch"
    required_landmarks = tuple(
        LandmarkName[f"{side.upper()}_{joint.upper()}"]
        for side in ("left", "right")
        for joint in _CRUNCH_BODY_JOINTS
    )
    _VISIBILITY_ALPHA = .28
    _SIGNAL_ALPHA = .46
    _SIDE_SWITCH_MARGIN = .08

    def __init__(self) -> None:
        self.counter = CrunchCounter()
        self._selected_side: str | None = None
        self._visibility_ema: dict[LandmarkName, float] = {}
        self._signal_ema: dict[str, float] = {}
        self._baseline_shoulder_hip: float | None = None
        self._baseline_nose_knee: float | None = None

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        timestamp = monotonic()
        visibility = self._smooth_visibility(landmarks)
        side, side_visibility, head = self._select_side(landmarks, visibility)
        if side is None or head is None:
            result = self.counter.update({}, {}, {}, timestamp)
            return ExerciseResult(
                result.count,
                result.state.value,
                f"Posture: BAD — {result.feedback}",
                {},
                result.debug_info,
            )

        shoulder = self._point(landmarks, side, "shoulder")
        hip = self._point(landmarks, side, "hip")
        knee = self._point(landmarks, side, "knee")
        ankle = self._point(landmarks, side, "ankle")
        if any(point is None for point in (shoulder, hip, knee, ankle)):
            result = self.counter.update({}, {}, {}, timestamp)
            return ExerciseResult(
                result.count,
                result.state.value,
                f"Posture: BAD — {result.feedback}",
                {},
                result.debug_info,
            )

        assert shoulder is not None and hip is not None and knee is not None and ankle is not None
        angles = self._aspect_corrected_joint_angles(landmarks)
        hip_angle = self._screen_angle(shoulder, hip, knee)
        torso_angle = self._line_angle(shoulder, hip)
        lower_body_angle = self._line_angle(hip, ankle)
        neck_angle = self._screen_angle(head, shoulder, hip)
        shoulder_lift = self._vertical_ratio(shoulder, hip)
        shoulder_hip_distance = self._pixel_distance(shoulder, hip)
        nose = landmarks.get(LandmarkName.NOSE, head)
        nose_knee_distance = self._pixel_distance(nose, knee)
        self._update_baselines(torso_angle, hip_angle, shoulder_hip_distance, nose_knee_distance)

        body_size, whole_body_inside = self._body_geometry(
            (head, shoulder, hip, knee, ankle)
        )
        body_rotation = self._body_rotation(landmarks, shoulder_hip_distance)
        raw_signals = {
            "Hip angle": hip_angle,
            "Torso flexion": max(0.0, 180.0 - hip_angle),
            "Torso angle": torso_angle,
            "Shoulder lift": shoulder_lift,
            "Lower body angle": lower_body_angle,
            "Neck angle": neck_angle,
            "Body rotation": body_rotation,
            "Body size": body_size,
            "Shoulder-hip ratio": self._distance_ratio(
                shoulder_hip_distance,
                self._baseline_shoulder_hip,
            ),
            "Nose-knee ratio": self._distance_ratio(
                nose_knee_distance,
                self._baseline_nose_knee,
            ),
        }
        signals = self._smooth_signals(raw_signals)
        signals["Whole body inside"] = float(whole_body_inside)

        selected_visibility = {
            "selected_head": visibility.get(self._head_name(side, landmarks), 0.0),
            **{
                f"selected_{joint}": visibility.get(self._landmark(side, joint), 0.0)
                for joint in _CRUNCH_BODY_JOINTS
            },
        }
        coordinates = {
            name.value: (point.x, point.y)
            for name, point in landmarks.items()
        }
        coordinates["selected_hip"] = (hip.x, hip.y)
        result = self.counter.update(signals, coordinates, selected_visibility, timestamp)

        posture = "GOOD" if result.posture_valid else "BAD"
        status = (
            f"Posture: {posture} — Form score: {result.form_score:.0f}% — "
            f"{result.feedback}"
        )
        debug = (
            f"{result.debug_info} | Selected side: {side} | "
            f"Visibility: {side_visibility:.0%} | Body size: {body_size:.0%}"
        )
        angles[f"{side.title()} hip"] = hip_angle
        angles["Torso flexion"] = signals["Torso flexion"]
        angles["Torso angle"] = signals["Torso angle"]
        angles["Neck alignment"] = signals["Neck angle"]
        return ExerciseResult(result.count, result.state.value, status, angles, debug)

    def _smooth_visibility(self, landmarks: PoseLandmarks) -> dict[LandmarkName, float]:
        names = [LandmarkName.NOSE]
        for side in ("left", "right"):
            names.append(self._landmark(side, "ear"))
            names.extend(self._landmark(side, joint) for joint in _CRUNCH_BODY_JOINTS)
        for name in names:
            current = landmarks[name].visibility if name in landmarks else 0.0
            previous = self._visibility_ema.get(name, current)
            self._visibility_ema[name] = (
                self._VISIBILITY_ALPHA * current
                + (1.0 - self._VISIBILITY_ALPHA) * previous
            )
        return self._visibility_ema

    def _select_side(
        self,
        landmarks: PoseLandmarks,
        visibility: dict[LandmarkName, float],
    ) -> tuple[str | None, float, Landmark | None]:
        scores: dict[str, float] = {}
        heads: dict[str, Landmark] = {}
        for side in ("left", "right"):
            names = tuple(self._landmark(side, joint) for joint in _CRUNCH_BODY_JOINTS)
            head_name = self._head_name(side, landmarks)
            if all(name in landmarks for name in names) and head_name in landmarks:
                body_values = [visibility.get(name, 0.0) for name in names]
                body_values.append(visibility.get(head_name, 0.0))
                scores[side] = sum(body_values) / len(body_values)
                heads[side] = landmarks[head_name]
        if not scores:
            return None, 0.0, None

        best = max(scores, key=scores.get)
        if (
            self._selected_side in scores
            and scores[self._selected_side] >= self.counter.cfg["visibility_threshold"]
            and scores[best] < scores[self._selected_side] + self._SIDE_SWITCH_MARGIN
        ):
            best = self._selected_side
        if best != self._selected_side:
            self._signal_ema.clear()
            self._baseline_shoulder_hip = None
            self._baseline_nose_knee = None
        self._selected_side = best
        return best, scores[best], heads[best]

    def _aspect_corrected_joint_angles(self, landmarks: PoseLandmarks) -> dict[str, float]:
        angles = calculate_joint_angles(landmarks)
        triples = {
            "shoulder": ("elbow", "shoulder", "hip"),
            "hip": ("shoulder", "hip", "knee"),
            "knee": ("hip", "knee", "ankle"),
        }
        for side in ("left", "right"):
            for joint, names in triples.items():
                points = tuple(self._landmark(side, name) for name in names)
                if all(point in landmarks for point in points):
                    angles[f"{side.title()} {joint}"] = self._screen_angle(
                        *(landmarks[point] for point in points)
                    )
        return angles

    def _update_baselines(
        self,
        torso_angle: float,
        hip_angle: float,
        shoulder_hip_distance: float,
        nose_knee_distance: float,
    ) -> None:
        lying = (
            torso_angle <= self.counter.cfg["lying_torso_angle"] + 5.0
            and hip_angle >= self.counter.cfg["start_angle"] - 25.0
        )
        if not lying:
            return
        self._baseline_shoulder_hip = self._smooth_baseline(
            self._baseline_shoulder_hip,
            shoulder_hip_distance,
        )
        self._baseline_nose_knee = self._smooth_baseline(
            self._baseline_nose_knee,
            nose_knee_distance,
        )

    @staticmethod
    def _smooth_baseline(previous: float | None, current: float) -> float:
        return current if previous is None else .08 * current + .92 * previous

    @staticmethod
    def _distance_ratio(current: float, baseline: float | None) -> float:
        return 1.0 if not baseline else current / baseline

    @staticmethod
    def _pixel_distance(a: Landmark, b: Landmark) -> float:
        return hypot(
            (a.x - b.x) * SETTINGS.camera_width,
            (a.y - b.y) * SETTINGS.camera_height,
        )

    @classmethod
    def _screen_angle(cls, a: Landmark, b: Landmark, c: Landmark) -> float:
        ab = (
            (a.x - b.x) * SETTINGS.camera_width,
            (a.y - b.y) * SETTINGS.camera_height,
        )
        cb = (
            (c.x - b.x) * SETTINGS.camera_width,
            (c.y - b.y) * SETTINGS.camera_height,
        )
        length_ab = hypot(*ab)
        length_cb = hypot(*cb)
        if length_ab == 0.0 or length_cb == 0.0:
            return 0.0
        cosine = max(
            -1.0,
            min(1.0, (ab[0] * cb[0] + ab[1] * cb[1]) / (length_ab * length_cb)),
        )
        return degrees(acos(cosine))

    @staticmethod
    def _line_angle(a: Landmark, b: Landmark) -> float:
        dx = (b.x - a.x) * SETTINGS.camera_width
        dy = (b.y - a.y) * SETTINGS.camera_height
        raw = abs(degrees(atan2(dy, dx)))
        return min(raw, abs(180.0 - raw))

    @classmethod
    def _vertical_ratio(cls, shoulder: Landmark, hip: Landmark) -> float:
        distance = cls._pixel_distance(shoulder, hip)
        if distance == 0.0:
            return 0.0
        return max(
            0.0,
            (hip.y - shoulder.y) * SETTINGS.camera_height / distance,
        )

    @staticmethod
    def _body_geometry(points: tuple[Landmark, ...]) -> tuple[float, bool]:
        horizontal_span = max(point.x for point in points) - min(point.x for point in points)
        vertical_span = max(point.y for point in points) - min(point.y for point in points)
        tolerance = .04
        inside = all(
            -tolerance <= point.x <= 1.0 + tolerance
            and -tolerance <= point.y <= 1.0 + tolerance
            for point in points
        )
        return max(horizontal_span, vertical_span), inside

    @classmethod
    def _body_rotation(cls, landmarks: PoseLandmarks, torso_length: float) -> float:
        if torso_length <= 0.0:
            return 90.0
        pairs = (
            (LandmarkName.LEFT_SHOULDER, LandmarkName.RIGHT_SHOULDER),
            (LandmarkName.LEFT_HIP, LandmarkName.RIGHT_HIP),
        )
        widths = [
            cls._pixel_distance(landmarks[left], landmarks[right])
            for left, right in pairs
            if left in landmarks
            and right in landmarks
            and landmarks[left].visibility >= .20
            and landmarks[right].visibility >= .20
        ]
        if not widths:
            return 0.0
        return min(90.0, sum(widths) / len(widths) / torso_length * 45.0)

    def _smooth_signals(self, current: dict[str, float]) -> dict[str, float]:
        for name, value in current.items():
            previous = self._signal_ema.get(name, value)
            self._signal_ema[name] = (
                self._SIGNAL_ALPHA * value
                + (1.0 - self._SIGNAL_ALPHA) * previous
            )
        return dict(self._signal_ema)

    @staticmethod
    def _point(
        landmarks: PoseLandmarks,
        side: str,
        joint: str,
    ) -> Landmark | None:
        return landmarks.get(CrunchDetector._landmark(side, joint))

    @staticmethod
    def _head_name(side: str, landmarks: PoseLandmarks) -> LandmarkName:
        ear = CrunchDetector._landmark(side, "ear")
        if (
            ear in landmarks
            and landmarks[ear].visibility
            >= landmarks.get(LandmarkName.NOSE, Landmark(0.0, 0.0, visibility=0.0)).visibility
        ):
            return ear
        return LandmarkName.NOSE

    @staticmethod
    def _landmark(side: str, joint: str) -> LandmarkName:
        return LandmarkName[f"{side.upper()}_{joint.upper()}"]

    def reset(self) -> None:
        self.counter.reset()
        self._selected_side = None
        self._visibility_ema.clear()
        self._signal_ema.clear()
        self._baseline_shoulder_hip = None
        self._baseline_nose_knee = None

    def get_repetitions(self) -> int:
        return self.counter.count


# Backward-compatible import name. The runtime class remains CrunchDetector,
# which is shown in Debug Mode and confirms the dedicated detector is loaded.
CrunchExercise = CrunchDetector
