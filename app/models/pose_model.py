from abc import ABC, abstractmethod
from typing import Any

from app.pose.pose_landmarks import PoseLandmarks


class PoseModel(ABC):
    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def predict(self, frame: Any) -> PoseLandmarks: ...

    @abstractmethod
    def close(self) -> None: ...
