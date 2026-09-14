from collections import deque
from math import acos, degrees
from typing import Iterable

from app.pose.pose_landmarks import Landmark, LandmarkName, PoseLandmarks


def calculate_angle(a: Landmark, b: Landmark, c: Landmark) -> float:
    """Return angle ABC in degrees; B is the joint."""
    ab = (a.x - b.x, a.y - b.y)
    cb = (c.x - b.x, c.y - b.y)
    mag_ab = (ab[0] ** 2 + ab[1] ** 2) ** 0.5
    mag_cb = (cb[0] ** 2 + cb[1] ** 2) ** 0.5
    if mag_ab == 0 or mag_cb == 0:
        return 0.0
    cosine = max(-1.0, min(1.0, (ab[0] * cb[0] + ab[1] * cb[1]) / (mag_ab * mag_cb)))
    return degrees(acos(cosine))


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
