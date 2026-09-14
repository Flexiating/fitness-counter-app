from app.exercises.crunch import CrunchExercise
from app.pose.pose_landmarks import Landmark, LandmarkName


def pose(shoulder_x: float, shoulder_y: float) -> dict[LandmarkName, Landmark]:
    return {
        LandmarkName.LEFT_SHOULDER: Landmark(shoulder_x, shoulder_y), LandmarkName.LEFT_HIP: Landmark(0, 0), LandmarkName.LEFT_KNEE: Landmark(1, 0),
        LandmarkName.RIGHT_SHOULDER: Landmark(shoulder_x, shoulder_y), LandmarkName.RIGHT_HIP: Landmark(0, 0), LandmarkName.RIGHT_KNEE: Landmark(1, 0),
    }


def test_crunch_counts_full_cycle() -> None:
    exercise = CrunchExercise()
    # hip angle: extended ≈180°, contracted ≈90°, extended
    for x, y in ((-1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)):
        for _ in range(3): result = exercise.process(pose(x, y))
    assert result.repetitions == 1
