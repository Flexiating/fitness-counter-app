from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.pose.pose_landmarks import LandmarkName, PoseLandmarks


@dataclass(frozen=True)
class ExerciseResult:
    repetitions: int
    state: str
    status: str
    angles: dict[str, float]
    debug: str = ""


class BaseExercise(ABC):
    name: str
    required_landmarks: tuple[LandmarkName, ...]

    @abstractmethod
    def process(self, landmarks: PoseLandmarks) -> ExerciseResult: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def get_repetitions(self) -> int: ...
