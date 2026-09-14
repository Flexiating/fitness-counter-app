from app.exercises.push_up import PushUpExercise
from app.pose.pose_landmarks import Landmark, LandmarkName


def pose(elbow_y: float) -> dict[LandmarkName, Landmark]:
    return {
        LandmarkName.LEFT_SHOULDER: Landmark(0, 0), LandmarkName.LEFT_ELBOW: Landmark(.5, elbow_y), LandmarkName.LEFT_WRIST: Landmark(1, 0),
        LandmarkName.RIGHT_SHOULDER: Landmark(0, 0), LandmarkName.RIGHT_ELBOW: Landmark(.5, elbow_y), LandmarkName.RIGHT_WRIST: Landmark(1, 0),
    }


def test_push_up_counts_full_cycle() -> None:
    exercise = PushUpExercise()
    # nearly straight elbow (UP), bent elbow (DOWN), then UP
    for y in (.01, .5, .01):
        for _ in range(3): result = exercise.process(pose(y))
    assert result.repetitions == 1


def test_push_up_waits_for_visible_body() -> None:
    result = PushUpExercise().process({})
    assert result.state == "WAITING" and result.repetitions == 0


def test_reset_clears_repetitions_and_motion_state() -> None:
    exercise = PushUpExercise()
    for y in (.01, .5, .01):
        for _ in range(3): exercise.process(pose(y))
    assert exercise.get_repetitions() == 1
    exercise.reset()
    assert exercise.get_repetitions() == 0
    # A return to UP alone after reset must not carry a prior DOWN state forward.
    for _ in range(3): result = exercise.process(pose(.01))
    assert result.repetitions == 0
