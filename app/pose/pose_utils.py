from collections import deque
from typing import Iterable

from app.pose.angles import angle as calculate_angle
from app.pose.pose_landmarks import Landmark, LandmarkName, PoseLandmarks


def landmarks_visible(landmarks: PoseLandmarks, required: Iterable[LandmarkName], minimum: float) -> bool:
    return all(name in landmarks and landmarks[name].visibility >= minimum for name in required)


class LandmarkSmoother:
    """Moving average smoother for normalized pose landmarks."""
    def __init__(self, window_size: int = 5) -> None:
        self._frames: deque[PoseLandmarks] = deque(maxlen=window_size)

    def update(self, landmarks: PoseLandmarks) -> PoseLandmarks:
        self._frames.append(landmarks)
        output: PoseLandmarks = {}
        for name, point in landmarks.items():
            points = [frame[name] for frame in self._frames if name in frame]
            if points:
                output[name] = Landmark(
                    sum(p.x for p in points) / len(points), sum(p.y for p in points) / len(points),
                    sum(p.z for p in points) / len(points), sum(p.visibility for p in points) / len(points),
                )
        return output

    def reset(self) -> None:
        self._frames.clear()
