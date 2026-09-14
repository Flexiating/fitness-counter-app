"""Pose-inference façade that keeps model details out of frame processing."""

from __future__ import annotations

from app.models.model_manager import ModelManager
from app.models.pose_model import PoseModel
from app.pose.pose_landmarks import PoseLandmarks


class PoseDetector:
    """Loads one pose model and returns standardized named landmarks per frame."""

    def __init__(self, model: PoseModel | None = None) -> None:
        self._manager = ModelManager(model)
        self._model: PoseModel | None = None

    def start(self) -> None:
        self._model = self._manager.start()

    def detect(self, frame: object) -> PoseLandmarks:
        if self._model is None:
            raise RuntimeError("Pose detector has not been started")
        return self._model.predict(frame)

    def close(self) -> None:
        self._manager.close()
        self._model = None
