from app.config.settings import SETTINGS
from app.pose.pose_landmarks import PoseLandmarks
from app.pose.pose_utils import LandmarkSmoother


class MotionProcessor:
    def __init__(self) -> None:
        self.smoother = LandmarkSmoother(SETTINGS.smoothing_window)

    def process(self, landmarks: PoseLandmarks) -> PoseLandmarks:
        return self.smoother.update(landmarks) if landmarks else {}

    def reset(self) -> None:
        self.smoother.reset()
