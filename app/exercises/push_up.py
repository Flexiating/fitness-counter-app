from __future__ import annotations

from math import acos, atan2, degrees
from time import monotonic

from app.config.settings import SETTINGS
from app.exercise.pushup_counter import PushUpCounter
from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.pose.angles import calculate_joint_angles
from app.pose.pose_landmarks import Landmark, LandmarkName, PoseLandmarks


_PUSHUP_JOINTS = ("shoulder", "elbow", "wrist", "hip", "knee", "ankle")


class PushUpExercise(BaseExercise):
    """Push-up analysis using the most visible body side and smoothed signals."""

    _JOINTS = _PUSHUP_JOINTS
    _VISIBILITY_ALPHA = .28
    _SIGNAL_ALPHA = .50
    _SIDE_SWITCH_MARGIN = .08

    required_landmarks = tuple(
        LandmarkName[f"{side.upper()}_{joint.upper()}"]
        for side in ("left", "right")
        for joint in _PUSHUP_JOINTS
    )
    name = "Push Up"

    def __init__(self) -> None:
        self.counter = PushUpCounter(
            SETTINGS.pushup_elbow_down,
            SETTINGS.pushup_elbow_up,
            SETTINGS.pushup_hip_tolerance,
            SETTINGS.pushup_debounce_seconds,
            SETTINGS.pushup_plank_max_orientation,
        )
        self._selected_side: str | None = None
        self._visibility_ema: dict[LandmarkName, float] = {}
        self._signal_ema: dict[str, float] = {}
        self._previous_alignment: tuple[float, float, float] | None = None
        self._score_ema: float | None = None

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        timestamp = monotonic()
        visibility = self._smooth_visibility(landmarks)
        side, side_visibility = self._select_side(landmarks, visibility)
        if side is None:
            result = self.counter.update({}, {}, timestamp)
            return ExerciseResult(
                result.repetitions,
                result.state.value,
                "Posture: BAD — No complete body side detected",
                {},
                self._debug(result, None, 0.0, 0.0),
            )

        angles = self._aspect_corrected_angles(landmarks)
        prefix = side.title()
        required_angles = (f"{prefix} elbow", f"{prefix} hip", f"{prefix} knee")
        if any(name not in angles for name in required_angles):
            result = self.counter.update({}, {}, timestamp)
            return ExerciseResult(
                result.repetitions,
                result.state.value,
                "Posture: BAD — Required joints unavailable",
                angles,
                self._debug(result, side, side_visibility, 0.0),
            )

        body_orientation = self._body_orientation(landmarks, side)
        back_alignment = self._back_alignment(landmarks, side)
        neck_alignment = self._neck_alignment(landmarks, side)
        body_size, whole_body_inside = self._body_geometry(landmarks, side)
        smoothed = self._smooth_signals({
            "Selected elbow": angles[f"{prefix} elbow"],
            "Selected hip": angles[f"{prefix} hip"],
            "Selected knee": angles[f"{prefix} knee"],
            "Body orientation": body_orientation,
            "Back alignment": back_alignment,
            "Body size": body_size,
        })
        stability = self._stability(smoothed)
        form_score = self._form_score(
            smoothed["Selected elbow"],
            smoothed["Selected hip"],
            smoothed["Back alignment"],
            neck_alignment,
            stability,
        )
        self._score_ema = form_score if self._score_ema is None else .22 * form_score + .78 * self._score_ema

        counter_angles = dict(angles)
        counter_angles.update(smoothed)
        counter_angles["Whole body inside"] = float(whole_body_inside)
        counter_angles["Form score"] = self._score_ema
        selected_visibility = {
            f"selected_{joint}": visibility.get(self._landmark(side, joint), 0.0)
            for joint in self._JOINTS
        }
        result = self.counter.update(counter_angles, selected_visibility, timestamp)

        status = f"Posture: {result.posture} — Form score: {result.form_score:.0f}%"
        if result.reason:
            status += f" — {result.reason}"
        debug = self._debug(result, side, side_visibility, body_size, selected_visibility, counter_angles)
        # Preserve the established angle payload. The extra detector signals
        # remain in the optional debug panel and do not add camera overlays.
        return ExerciseResult(result.repetitions, result.state.value, status, angles, debug)

    def _smooth_visibility(self, landmarks: PoseLandmarks) -> dict[LandmarkName, float]:
        names = tuple(self._landmark(side, joint) for side in ("left", "right") for joint in self._JOINTS)
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
    ) -> tuple[str | None, float]:
        scores: dict[str, float] = {}
        for side in ("left", "right"):
            names = tuple(self._landmark(side, joint) for joint in self._JOINTS)
            if all(name in landmarks for name in names):
                scores[side] = sum(visibility.get(name, 0.0) for name in names) / len(names)
        if not scores:
            return None, 0.0

        best = max(scores, key=scores.get)
        if (
            self._selected_side in scores
            and scores[self._selected_side] >= .45
            and scores[best] < scores[self._selected_side] + self._SIDE_SWITCH_MARGIN
        ):
            best = self._selected_side
        if best != self._selected_side:
            self._signal_ema.clear()
            self._previous_alignment = None
        self._selected_side = best
        return best, scores[best]

    def _aspect_corrected_angles(self, landmarks: PoseLandmarks) -> dict[str, float]:
        angles = calculate_joint_angles(landmarks)
        triples = {
            "elbow": ("shoulder", "elbow", "wrist"),
            "shoulder": ("elbow", "shoulder", "hip"),
            "hip": ("shoulder", "hip", "knee"),
            "knee": ("hip", "knee", "ankle"),
        }
        for side in ("left", "right"):
            for joint, points in triples.items():
                names = tuple(self._landmark(side, point) for point in points)
                if all(name in landmarks for name in names):
                    angles[f"{side.title()} {joint}"] = self._screen_angle(
                        *(landmarks[name] for name in names)
                    )
        return angles

    @staticmethod
    def _screen_angle(a: Landmark, b: Landmark, c: Landmark) -> float:
        """Return angle ABC in camera-pixel space without aspect distortion."""
        width, height = SETTINGS.camera_width, SETTINGS.camera_height
        ab = ((a.x - b.x) * width, (a.y - b.y) * height)
        cb = ((c.x - b.x) * width, (c.y - b.y) * height)
        length_ab = (ab[0] ** 2 + ab[1] ** 2) ** .5
        length_cb = (cb[0] ** 2 + cb[1] ** 2) ** .5
        if length_ab == 0.0 or length_cb == 0.0:
            return 0.0
        cosine = max(
            -1.0,
            min(1.0, (ab[0] * cb[0] + ab[1] * cb[1]) / (length_ab * length_cb)),
        )
        return degrees(acos(cosine))

    @classmethod
    def _body_orientation(cls, landmarks: PoseLandmarks, side: str) -> float:
        shoulder = landmarks[cls._landmark(side, "shoulder")]
        hip = landmarks[cls._landmark(side, "hip")]
        dx = (hip.x - shoulder.x) * SETTINGS.camera_width
        dy = (hip.y - shoulder.y) * SETTINGS.camera_height
        raw = abs(degrees(atan2(dy, dx)))
        return min(raw, abs(180.0 - raw))

    @classmethod
    def _back_alignment(cls, landmarks: PoseLandmarks, side: str) -> float:
        return cls._screen_angle(
            landmarks[cls._landmark(side, "shoulder")],
            landmarks[cls._landmark(side, "hip")],
            landmarks[cls._landmark(side, "ankle")],
        )

    @classmethod
    def _neck_alignment(cls, landmarks: PoseLandmarks, side: str) -> float:
        ear = cls._landmark(side, "ear")
        shoulder = cls._landmark(side, "shoulder")
        hip = cls._landmark(side, "hip")
        if ear not in landmarks or landmarks[ear].visibility < .20:
            return 165.0
        return cls._screen_angle(
            landmarks[ear],
            landmarks[shoulder],
            landmarks[hip],
        )

    @classmethod
    def _body_geometry(cls, landmarks: PoseLandmarks, side: str) -> tuple[float, bool]:
        names = [cls._landmark(side, joint) for joint in cls._JOINTS]
        head = cls._landmark(side, "ear")
        if head in landmarks and landmarks[head].visibility >= .20:
            names.append(head)
        points = [landmarks[name] for name in names]
        horizontal_span = max(point.x for point in points) - min(point.x for point in points)
        vertical_span = max(point.y for point in points) - min(point.y for point in points)
        body_size = max(horizontal_span, vertical_span)
        tolerance = .04
        inside = all(
            -tolerance <= point.x <= 1.0 + tolerance
            and -tolerance <= point.y <= 1.0 + tolerance
            for point in points
        )
        return body_size, inside

    def _smooth_signals(self, current: dict[str, float]) -> dict[str, float]:
        for name, value in current.items():
            previous = self._signal_ema.get(name, value)
            self._signal_ema[name] = (
                self._SIGNAL_ALPHA * value
                + (1.0 - self._SIGNAL_ALPHA) * previous
            )
        return dict(self._signal_ema)

    def _stability(self, signals: dict[str, float]) -> float:
        current = (
            signals["Selected hip"],
            signals["Back alignment"],
            signals["Body orientation"],
        )
        if self._previous_alignment is None:
            score = 100.0
        else:
            change = sum(
                abs(value - old)
                for value, old in zip(current, self._previous_alignment)
            ) / len(current)
            score = max(0.0, 100.0 - change * 4.0)
        self._previous_alignment = current
        return score

    @classmethod
    def _form_score(
        cls,
        elbow: float,
        hip: float,
        back: float,
        neck: float,
        stability: float,
    ) -> float:
        return (
            .25 * cls._elbow_score(elbow)
            + .25 * cls._straight_score(hip)
            + .25 * cls._straight_score(back)
            + .10 * cls._straight_score(neck)
            + .15 * stability
        )

    @staticmethod
    def _elbow_score(value: float) -> float:
        if value >= 170.0:
            return 100.0
        if value >= 165.0:
            return 92.0 + (value - 165.0) * 1.6
        if value >= 160.0:
            return 84.0 + (value - 160.0) * 1.6
        if value >= 150.0:
            return 70.0 + (value - 150.0) * 1.4
        if value <= 95.0:
            return max(70.0, 100.0 - max(0.0, value - 70.0) * 1.2)
        return 70.0

    @staticmethod
    def _straight_score(value: float) -> float:
        if value >= 170.0:
            return 100.0
        if value >= 165.0:
            return 92.0 + (value - 165.0) * 1.6
        if value >= 160.0:
            return 84.0 + (value - 160.0) * 1.6
        if value >= 150.0:
            return 70.0 + (value - 150.0) * 1.4
        if value >= 140.0:
            return 50.0 + (value - 140.0) * 2.0
        return max(0.0, value - 90.0)

    @staticmethod
    def _landmark(side: str, joint: str) -> LandmarkName:
        return LandmarkName[f"{side.upper()}_{joint.upper()}"]

    def _debug(
        self,
        result,
        side: str | None,
        side_visibility: float,
        body_size: float,
        selected_visibility: dict[str, float] | None = None,
        signals: dict[str, float] | None = None,
    ) -> str:
        signals = signals or {}
        selected_visibility = selected_visibility or {}
        weakest = min(selected_visibility.values()) if selected_visibility else 0.0
        return (
            f"Push-up debug | state={result.state.value} | side={side or 'none'} | "
            f"elbow={signals.get('Selected elbow', 0.0):.1f}° | "
            f"hip={signals.get('Selected hip', 0.0):.1f}° | "
            f"back={signals.get('Back alignment', 0.0):.1f}° | "
            f"orientation={signals.get('Body orientation', 0.0):.1f}° | "
            f"body size={body_size:.0%} | visibility={side_visibility:.0%} "
            f"(min {weakest:.0%}) | form={result.form_score:.0f}% | "
            f"last={result.last_transition} | rejected={result.reason or 'none'}"
        )

    def reset(self) -> None:
        self.counter.reset()
        self._selected_side = None
        self._visibility_ema.clear()
        self._signal_ema.clear()
        self._previous_alignment = None
        self._score_ema = None

    def get_repetitions(self) -> int:
        return self.counter.repetitions
