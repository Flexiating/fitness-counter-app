from app.config.settings import SETTINGS
from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.pose.pose_landmarks import LandmarkName, PoseLandmarks
from app.pose.pose_utils import calculate_angle, landmarks_visible
from app.processing.repetition_counter import MovementState, RepetitionCounter


class PushUpExercise(BaseExercise):
    name = "Push Up"
    required_landmarks = (LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_ELBOW, LandmarkName.LEFT_WRIST,
                          LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_ELBOW, LandmarkName.RIGHT_WRIST)

    def __init__(self) -> None:
        self.counter = RepetitionCounter(SETTINGS.minimum_state_frames)

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        if not landmarks_visible(landmarks, self.required_landmarks, SETTINGS.min_visibility):
            return ExerciseResult(self.counter.repetitions, "WAITING", "Move into camera view", {})
        left = calculate_angle(landmarks[LandmarkName.LEFT_SHOULDER], landmarks[LandmarkName.LEFT_ELBOW], landmarks[LandmarkName.LEFT_WRIST])
        right = calculate_angle(landmarks[LandmarkName.RIGHT_SHOULDER], landmarks[LandmarkName.RIGHT_ELBOW], landmarks[LandmarkName.RIGHT_WRIST])
        angle = max(left, right)  # the clearer side is usually less occluded
        observed = MovementState.EXTENDED if angle >= SETTINGS.push_up_up_threshold else (MovementState.CONTRACTED if angle <= SETTINGS.push_up_down_threshold else None)
        reps = self.counter.update(observed)
        state = "UP" if observed is MovementState.EXTENDED else ("DOWN" if observed is MovementState.CONTRACTED else "MOVING")
        return ExerciseResult(reps, state, "Ready" if observed else "Complete the movement", {"elbow": angle})

    def reset(self) -> None:
        self.counter.reset()

    def get_repetitions(self) -> int:
        return self.counter.repetitions
