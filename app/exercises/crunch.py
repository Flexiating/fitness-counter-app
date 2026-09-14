from app.config.settings import SETTINGS
from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.pose.pose_landmarks import LandmarkName, PoseLandmarks
from app.pose.pose_utils import calculate_angle, landmarks_visible
from app.processing.repetition_counter import MovementState, RepetitionCounter


class CrunchExercise(BaseExercise):
    name = "Crunch"
    required_landmarks = (LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_HIP, LandmarkName.LEFT_KNEE,
                          LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_HIP, LandmarkName.RIGHT_KNEE)

    def __init__(self) -> None:
        self.counter = RepetitionCounter(SETTINGS.minimum_state_frames)

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        if not landmarks_visible(landmarks, self.required_landmarks, SETTINGS.min_visibility):
            return ExerciseResult(self.counter.repetitions, "WAITING", "Move farther from the camera", {})
        left = calculate_angle(landmarks[LandmarkName.LEFT_SHOULDER], landmarks[LandmarkName.LEFT_HIP], landmarks[LandmarkName.LEFT_KNEE])
        right = calculate_angle(landmarks[LandmarkName.RIGHT_SHOULDER], landmarks[LandmarkName.RIGHT_HIP], landmarks[LandmarkName.RIGHT_KNEE])
        angle = (left + right) / 2
        observed = MovementState.EXTENDED if angle >= SETTINGS.crunch_extended_threshold else (MovementState.CONTRACTED if angle <= SETTINGS.crunch_contracted_threshold else None)
        reps = self.counter.update(observed)
        state = "EXTENDED" if observed is MovementState.EXTENDED else ("CONTRACTED" if observed is MovementState.CONTRACTED else "MOVING")
        return ExerciseResult(reps, state, "Ready" if observed else "Complete the movement", {"hip": angle})

    def reset(self) -> None:
        self.counter.reset()

    def get_repetitions(self) -> int:
        return self.counter.repetitions
