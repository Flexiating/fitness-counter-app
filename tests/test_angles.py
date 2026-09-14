from app.pose.pose_landmarks import Landmark, LandmarkName
from app.pose.pose_utils import LandmarkSmoother, calculate_angle, landmarks_visible
from app.utils.math_utils import distance


def test_angle_and_distance() -> None:
    a, b, c = Landmark(1, 0), Landmark(0, 0), Landmark(0, 1)
    assert calculate_angle(a, b, c) == 90.0
    assert distance(a, b) == 1.0


def test_visibility_and_smoothing() -> None:
    name = LandmarkName.LEFT_ELBOW
    assert landmarks_visible({name: Landmark(0, 0, visibility=.7)}, [name], .5)
    smoother = LandmarkSmoother(2)
    smoother.update({name: Landmark(0, 0)})
    assert smoother.update({name: Landmark(1, 1)})[name] == Landmark(.5, .5, 0.0, 1.0)
