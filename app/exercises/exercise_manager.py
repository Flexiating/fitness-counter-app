from threading import Lock

from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.exercises.crunch import CrunchExercise
from app.exercises.push_up import PushUpExercise
from app.pose.pose_landmarks import PoseLandmarks


class ExerciseManager:
    def __init__(self) -> None:
        self._exercises: dict[str, BaseExercise] = {"push_up": PushUpExercise(), "crunch": CrunchExercise()}
        self._selected = "push_up"
        self._lock = Lock()

    @property
    def names(self) -> dict[str, str]:
        return {key: item.name for key, item in self._exercises.items()}

    @property
    def selected(self) -> BaseExercise:
        with self._lock:
            return self._exercises[self._selected]

    def select(self, key: str) -> None:
        if key not in self._exercises:
            raise KeyError(f"Unknown exercise: {key}")
        with self._lock:
            self._selected = key
            self._exercises[key].reset()

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        with self._lock:
            return self._exercises[self._selected].process(landmarks)

    def reset(self) -> None:
        with self._lock:
            self._exercises[self._selected].reset()

    def repetitions(self) -> int:
        with self._lock:
            return self._exercises[self._selected].get_repetitions()
