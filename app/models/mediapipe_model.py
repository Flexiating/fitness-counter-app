from typing import Any

import cv2
import mediapipe as mp

from app.config.settings import SETTINGS
from app.models.pose_model import PoseModel
from app.pose.pose_landmarks import Landmark, LandmarkName, PoseLandmarks


class MediaPipePoseModel(PoseModel):
    """Adapter that shields the rest of the application from MediaPipe APIs."""
    _mapping = {
        LandmarkName.NOSE: 0, LandmarkName.LEFT_SHOULDER: 11, LandmarkName.RIGHT_SHOULDER: 12,
        LandmarkName.LEFT_ELBOW: 13, LandmarkName.RIGHT_ELBOW: 14, LandmarkName.LEFT_WRIST: 15,
        LandmarkName.RIGHT_WRIST: 16, LandmarkName.LEFT_HIP: 23, LandmarkName.RIGHT_HIP: 24,
        LandmarkName.LEFT_KNEE: 25, LandmarkName.RIGHT_KNEE: 26, LandmarkName.LEFT_ANKLE: 27,
        LandmarkName.RIGHT_ANKLE: 28,
    }

    def __init__(self) -> None:
        self._pose: Any = None

    def load(self) -> None:
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False, model_complexity=1, enable_segmentation=False,
            min_detection_confidence=SETTINGS.pose_min_confidence,
            min_tracking_confidence=SETTINGS.pose_tracking_confidence,
        )

    def predict(self, frame: Any) -> PoseLandmarks:
        if self._pose is None:
            raise RuntimeError("Pose model has not been loaded")
        result = self._pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not result.pose_landmarks:
            return {}
        raw = result.pose_landmarks.landmark
        return {name: Landmark(raw[index].x, raw[index].y, raw[index].z, raw[index].visibility)
                for name, index in self._mapping.items()}

    def close(self) -> None:
        if self._pose:
            self._pose.close()
            self._pose = None
