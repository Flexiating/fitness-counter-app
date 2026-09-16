from app.exercises.push_up import PushUpExercise
from app.pose.pose_landmarks import Landmark, LandmarkName


def pose(elbow_angle: str = "up", left_visibility: float = .95, right_visibility: float = .2):
    result = {}
    for side, offset, visibility in (
        ("LEFT", 0.0, left_visibility),
        ("RIGHT", .04, right_visibility),
    ):
        points = {
            "SHOULDER": (.25, .45 + offset),
            "ELBOW": (.25, .60 + offset),
            "WRIST": (.25, .75 + offset),
            "HIP": (.50, .50 + offset),
            "KNEE": (.68, .536 + offset),
            "ANKLE": (.85, .57 + offset),
            "EAR": (.16, .432 + offset),
        }
        if elbow_angle == "down":
            points["WRIST"] = (.35, .60 + offset)
        elif elbow_angle == "partial":
            points["WRIST"] = (.31, .68 + offset)
        for joint, (x, y) in points.items():
            result[LandmarkName[f"{side}_{joint}"]] = Landmark(x, y, visibility=visibility)
    return result


def timeline(monkeypatch, values):
    monkeypatch.setattr("app.exercises.push_up.monotonic", iter(values).__next__)


def test_push_up_waits_for_visible_body() -> None:
    result = PushUpExercise().process({})
    assert result.state == "WAITING" and result.repetitions == 0


def test_push_up_chooses_the_more_visible_side() -> None:
    exercise = PushUpExercise()
    result = exercise.process(pose(left_visibility=.2, right_visibility=.92))
    assert "side=right" in result.debug
    assert "No complete body side" not in result.status


def test_temporary_far_side_occlusion_does_not_reject_correct_alignment(monkeypatch) -> None:
    exercise = PushUpExercise()
    timeline(monkeypatch, (0.0, .1, .21))
    first = exercise.process(pose())
    exercise.process(pose(left_visibility=.60, right_visibility=.05))
    stable = exercise.process(pose(left_visibility=.95, right_visibility=.05))
    assert first.state == "READY"
    assert stable.state == "UP"
    assert "Posture: BAD" not in stable.status


def test_push_up_adapter_counts_a_smoothed_complete_rep(monkeypatch) -> None:
    exercise = PushUpExercise()
    times = [index * .11 for index in range(22)]
    timeline(monkeypatch, times)

    results = []
    for _ in range(3):
        results.append(exercise.process(pose("up")))
    for _ in range(8):
        results.append(exercise.process(pose("down")))
    for _ in range(11):
        results.append(exercise.process(pose("up")))

    assert any(result.state == "DOWN" for result in results)
    assert results[-1].state == "UP"
    assert results[-1].repetitions == 1


def test_aspect_corrected_angle_uses_camera_pixel_geometry() -> None:
    width, height = 960.0, 540.0
    center = Landmark(.5, .5)
    horizontal = Landmark(.5 + 100.0 / width, .5)
    diagonal = Landmark(.5 + 100.0 / width, .5 + 100.0 / height)
    assert PushUpExercise._screen_angle(horizontal, center, diagonal) == 45.0
