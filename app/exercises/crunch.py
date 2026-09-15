from time import monotonic

from app.exercise.crunch_counter import CrunchCounter
from app.config.settings import SETTINGS
from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.pose.angles import calculate_joint_angles
from app.pose.pose_landmarks import LandmarkName, PoseLandmarks
from app.pose.pose_utils import landmarks_visible


class CrunchExercise(BaseExercise):
    name = "Crunch"
    required_landmarks = (LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_HIP, LandmarkName.LEFT_KNEE,
                          LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_HIP, LandmarkName.RIGHT_KNEE)

    def __init__(self) -> None:
        self.counter = CrunchCounter()

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        if not landmarks_visible(landmarks, self.required_landmarks, SETTINGS.min_visibility):
            return ExerciseResult(self.counter.count, "WAITING", "Move farther from the camera", {})
        angles = calculate_joint_angles(landmarks)
        coords = {name.value: (point.x, point.y) for name, point in landmarks.items()}
        visibility = {name.value: point.visibility for name, point in landmarks.items()}
        result = self.counter.update(angles, coords, visibility, monotonic())
        return ExerciseResult(result.count, result.state.value, result.feedback, angles, result.debug_info)

    def reset(self) -> None:
        self.counter.reset()

    def get_repetitions(self) -> int:
        return self.counter.count
