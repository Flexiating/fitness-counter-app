from typing import Any

from app.config.settings import SETTINGS
from app.models.pose_model import PoseModel
from app.pose.pose_landmarks import Landmark, LandmarkName, PoseLandmarks


class MediaPipePoseModel(PoseModel):
    """Adapter that shields the rest of the application from MediaPipe APIs."""
    _mapping = {
        LandmarkName.NOSE: 0, LandmarkName.LEFT_EYE_INNER: 1, LandmarkName.LEFT_EYE: 2,
        LandmarkName.LEFT_EYE_OUTER: 3, LandmarkName.RIGHT_EYE_INNER: 4, LandmarkName.RIGHT_EYE: 5,
        LandmarkName.RIGHT_EYE_OUTER: 6, LandmarkName.LEFT_EAR: 7, LandmarkName.RIGHT_EAR: 8,
        LandmarkName.MOUTH_LEFT: 9, LandmarkName.MOUTH_RIGHT: 10,
        LandmarkName.LEFT_SHOULDER: 11, LandmarkName.RIGHT_SHOULDER: 12,
        LandmarkName.LEFT_ELBOW: 13, LandmarkName.RIGHT_ELBOW: 14, LandmarkName.LEFT_WRIST: 15,
        LandmarkName.RIGHT_WRIST: 16, LandmarkName.LEFT_PINKY: 17, LandmarkName.RIGHT_PINKY: 18,
        LandmarkName.LEFT_INDEX: 19, LandmarkName.RIGHT_INDEX: 20, LandmarkName.LEFT_THUMB: 21,
        LandmarkName.RIGHT_THUMB: 22, LandmarkName.LEFT_HIP: 23, LandmarkName.RIGHT_HIP: 24,
        LandmarkName.LEFT_KNEE: 25, LandmarkName.RIGHT_KNEE: 26, LandmarkName.LEFT_ANKLE: 27,
        LandmarkName.RIGHT_ANKLE: 28, LandmarkName.LEFT_HEEL: 29, LandmarkName.RIGHT_HEEL: 30,
        LandmarkName.LEFT_FOOT_INDEX: 31, LandmarkName.RIGHT_FOOT_INDEX: 32,
    }

    def __init__(self) -> None:
        self._pose: Any = None
        self._cv2: Any = None

    def load(self) -> None:
        import cv2
        import mediapipe as mp

        self._cv2 = cv2
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=SETTINGS.pose_model_complexity,
            enable_segmentation=False,
            min_detection_confidence=SETTINGS.pose_min_confidence,
            min_tracking_confidence=SETTINGS.pose_tracking_confidence,
        )

    def predict(self, frame: Any) -> PoseLandmarks:
        if self._pose is None or self._cv2 is None:
            raise RuntimeError("Pose model has not been loaded")
        result = self._pose.process(self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB))
        if not result.pose_landmarks:
            return {}
        raw = result.pose_landmarks.landmark
        return {name: Landmark(raw[index].x, raw[index].y, raw[index].z, raw[index].visibility)
                for name, index in self._mapping.items()}

    def close(self) -> None:
        try:
            if self._pose:
                self._pose.close()
        finally:
            self._pose = None
            self._cv2 = None
