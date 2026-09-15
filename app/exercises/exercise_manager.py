from threading import Lock

from app.exercises.base_exercise import BaseExercise, ExerciseResult
from app.exercises.crunch import CrunchExercise
from app.exercises.push_up import PushUpExercise
from app.pose.pose_landmarks import PoseLandmarks


class ExerciseManager:
    def __init__(self) -> None:
        self._exercises: dict[str, BaseExercise] = {"push_up": PushUpExercise(), "crunch": CrunchExercise()}
        self._selected = "push_up"
        self._generation = 0
        self._lock = Lock()

    @property
    def names(self) -> dict[str, str]:
        return {key: item.name for key, item in self._exercises.items()}

    @property
    def selected(self) -> BaseExercise:
        with self._lock:
            return self._exercises[self._selected]

    def select(self, key: str) -> None:
        with self._lock:
            if key not in self._exercises:
                raise KeyError(f"Unknown exercise: {key}")
            self._selected = key
            self._exercises[key].reset()
            self._generation += 1

    def process(self, landmarks: PoseLandmarks) -> ExerciseResult:
        with self._lock:
            return self._exercises[self._selected].process(landmarks)

    def process_snapshot(self, landmarks: PoseLandmarks) -> tuple[int, ExerciseResult]:
        """Return a result tagged with the current counter generation.

        The UI uses the generation to ignore results that were queued before an
        exercise switch or reset.
        """
        with self._lock:
            generation = self._generation
            result = self._exercises[self._selected].process(landmarks)
            return generation, result

    def reset(self) -> None:
        with self._lock:
            self._exercises[self._selected].reset()
            self._generation += 1

    def repetitions(self) -> int:
        with self._lock:
            return self._exercises[self._selected].get_repetitions()

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation
