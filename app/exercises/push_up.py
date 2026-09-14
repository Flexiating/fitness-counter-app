from math import atan2, degrees
from time import monotonic

from app.config.settings import SETTINGS
from app.exercise.pushup_counter import PushUpCounter
from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.pose.angles import calculate_joint_angles
from app.pose.pose_landmarks import LandmarkName, PoseLandmarks
from app.pose.pose_utils import landmarks_visible


class PushUpExercise(BaseExercise):
    name = "Push Up"
    required_landmarks = (LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_ELBOW, LandmarkName.LEFT_WRIST,
                          LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_ELBOW, LandmarkName.RIGHT_WRIST,
                          LandmarkName.LEFT_HIP, LandmarkName.RIGHT_HIP,
                          LandmarkName.LEFT_KNEE, LandmarkName.RIGHT_KNEE)

    def __init__(self) -> None:
        self.counter = PushUpCounter(SETTINGS.pushup_elbow_down, SETTINGS.pushup_elbow_up,
                                     SETTINGS.pushup_hip_tolerance, SETTINGS.pushup_debounce_seconds,
                                     SETTINGS.pushup_plank_max_orientation)

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        if not landmarks_visible(landmarks, self.required_landmarks, SETTINGS.min_visibility):
            return ExerciseResult(self.counter.repetitions, "WAITING", "Move into camera view", {})
        angles = calculate_joint_angles(landmarks)
        angles["Body orientation"] = self._body_orientation(landmarks)
        visibility = {name.value: point.visibility for name, point in landmarks.items()}
        result = self.counter.update(angles, visibility, monotonic())
        status = "Posture: " + result.posture
        if result.reason:
            status += f" — {result.reason}"
        debug = (f"Push-up debug — state: {result.state.value}; last transition: {result.last_transition}; "
                 f"thresholds: down {self.counter.elbow_down:.0f}°, up {self.counter.elbow_up:.0f}°, "
                 f"hip tolerance ±{self.counter.hip_tolerance:.0f}°; rejected: {result.reason or 'none'}")
        return ExerciseResult(result.repetitions, result.state.value, status, angles, debug)

    @staticmethod
    def _body_orientation(landmarks: PoseLandmarks) -> float:
        """0° is horizontal plank alignment; 90° is upright standing alignment."""
        shoulder = landmarks[LandmarkName.LEFT_SHOULDER]
        hip = landmarks[LandmarkName.LEFT_HIP]
        raw = abs(degrees(atan2(hip.y - shoulder.y, hip.x - shoulder.x)))
        return min(raw, abs(180.0 - raw))

    def reset(self) -> None:
        self.counter.reset()

    def get_repetitions(self) -> int:
        return self.counter.repetitions
