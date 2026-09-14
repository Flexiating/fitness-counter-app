from __future__ import annotations

from app.models.mediapipe_model import MediaPipePoseModel
from app.models.pose_model import PoseModel


class ModelManager:
    def __init__(self, model: PoseModel | None = None) -> None:
        self.model = model or MediaPipePoseModel()

    def start(self) -> PoseModel:
        self.model.load()
        return self.model

    def close(self) -> None:
        self.model.close()
