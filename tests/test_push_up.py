from app.exercises.push_up import PushUpExercise
from app.pose.pose_landmarks import Landmark, LandmarkName


def pose(elbow_y: float) -> dict[LandmarkName, Landmark]:
    return {
        LandmarkName.LEFT_SHOULDER: Landmark(0, 0), LandmarkName.LEFT_ELBOW: Landmark(.5, elbow_y), LandmarkName.LEFT_WRIST: Landmark(1, 0),
        LandmarkName.RIGHT_SHOULDER: Landmark(0, 0), LandmarkName.RIGHT_ELBOW: Landmark(.5, elbow_y), LandmarkName.RIGHT_WRIST: Landmark(1, 0),
        LandmarkName.LEFT_HIP: Landmark(.5, 0), LandmarkName.RIGHT_HIP: Landmark(.5, 0),
        LandmarkName.LEFT_KNEE: Landmark(1, 0), LandmarkName.RIGHT_KNEE: Landmark(1, 0),
    }


def test_push_up_waits_for_visible_body() -> None:
    result = PushUpExercise().process({})
    assert result.state == "WAITING" and result.repetitions == 0


def test_push_up_adapter_reports_invalid_posture_without_counting() -> None:
    result = PushUpExercise().process(pose(.01))
    assert result.repetitions == 0
