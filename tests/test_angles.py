from app.pose.pose_landmarks import Landmark, LandmarkName
from app.pose.angles import angle, calculate_joint_angles
from app.pose.pose_utils import LandmarkSmoother, calculate_angle, landmarks_visible
from app.utils.math_utils import distance


def test_angle_and_distance() -> None:
    a, b, c = Landmark(1, 0), Landmark(0, 0), Landmark(0, 1)
    assert calculate_angle(a, b, c) == 90.0
    assert distance(a, b) == 1.0


def test_generic_angle_is_bounded_and_joint_angles_are_bilateral() -> None:
    a, b, c = Landmark(1, 0), Landmark(0, 0), Landmark(-1, 0)
    assert angle(a, b, c) == 180.0
    pose = {
        LandmarkName.LEFT_SHOULDER: Landmark(0, 0), LandmarkName.LEFT_ELBOW: Landmark(.5, 0), LandmarkName.LEFT_WRIST: Landmark(1, 0),
        LandmarkName.RIGHT_SHOULDER: Landmark(0, .1), LandmarkName.RIGHT_ELBOW: Landmark(.5, .1), LandmarkName.RIGHT_WRIST: Landmark(1, .1),
        LandmarkName.LEFT_HIP: Landmark(0, .5), LandmarkName.RIGHT_HIP: Landmark(0, .6),
        LandmarkName.LEFT_KNEE: Landmark(.5, .8), LandmarkName.RIGHT_KNEE: Landmark(.5, .9),
        LandmarkName.LEFT_ANKLE: Landmark(.8, 1), LandmarkName.RIGHT_ANKLE: Landmark(.8, 1),
    }
    assert len(calculate_joint_angles(pose)) == 8


def test_visibility_and_smoothing() -> None:
    name = LandmarkName.LEFT_ELBOW
    assert landmarks_visible({name: Landmark(0, 0, visibility=.7)}, [name], .5)
    smoother = LandmarkSmoother(2)
    smoother.update({name: Landmark(0, 0)})
    assert smoother.update({name: Landmark(1, 1)})[name] == Landmark(.5, .5, 0.0, 1.0)
