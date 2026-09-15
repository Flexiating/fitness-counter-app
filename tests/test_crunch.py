from app.exercises.crunch import CrunchDetector, CrunchExercise
from app.pose.pose_landmarks import Landmark, LandmarkName


def pose(stage: str = "down", left_visibility: float = .95, right_visibility: float = .30):
    if stage == "up":
        base = {
            "EAR": (.38, .50),
            "SHOULDER": (.46, .54),
            "HIP": (.55, .70),
            "KNEE": (.72, .48),
            "ANKLE": (.82, .70),
        }
        nose = (.35, .48)
    elif stage == "partial":
        base = {
            "EAR": (.31, .60),
            "SHOULDER": (.42, .64),
            "HIP": (.55, .70),
            "KNEE": (.72, .48),
            "ANKLE": (.82, .70),
        }
        nose = (.28, .58)
    else:
        base = {
            "EAR": (.25, .67),
            "SHOULDER": (.35, .70),
            "HIP": (.55, .70),
            "KNEE": (.72, .48),
            "ANKLE": (.82, .70),
        }
        nose = (.22, .65)

    result = {LandmarkName.NOSE: Landmark(*nose, visibility=left_visibility)}
    for side, offset, visibility in (
        ("LEFT", 0.0, left_visibility),
        ("RIGHT", .012, right_visibility),
    ):
        for joint, (x, y) in base.items():
            result[LandmarkName[f"{side}_{joint}"]] = Landmark(
                x,
                y + offset,
                visibility=visibility,
            )
    return result


def timeline(monkeypatch, count, step=.11):
    monkeypatch.setattr(
        "app.exercises.crunch.monotonic",
        iter(index * step for index in range(count)).__next__,
    )


def test_crunch_detector_is_a_dedicated_runtime_class() -> None:
    exercise = CrunchExercise()
    assert type(exercise).__name__ == "CrunchDetector"
    assert isinstance(exercise, CrunchDetector)


def test_crunch_waits_for_visible_body_without_crashing() -> None:
    result = CrunchDetector().process({})
    assert result.state == "WAITING"
    assert result.repetitions == 0
    assert "CrunchDetector" in result.debug


def test_crunch_selects_visible_side_and_uses_torso_angles() -> None:
    result = CrunchDetector().process(
        pose("down", left_visibility=.25, right_visibility=.92)
    )
    assert "Selected side: right" in result.debug
    assert "Torso flexion" in result.angles
    assert "Left elbow" not in result.debug


def test_crunch_detector_counts_lying_lifted_lying_cycle(monkeypatch) -> None:
    detector = CrunchDetector()
    timeline(monkeypatch, 30)
    results = []
    for _ in range(5):
        results.append(detector.process(pose("down")))
    for _ in range(11):
        results.append(detector.process(pose("up")))
    for _ in range(14):
        results.append(detector.process(pose("down")))

    assert any(result.state == "UP" for result in results)
    assert results[-1].state == "DOWN"
    assert results[-1].repetitions == 1
    assert "Form score:" in results[-1].status


def test_partial_crunch_never_reaches_up(monkeypatch) -> None:
    detector = CrunchDetector()
    timeline(monkeypatch, 20)
    results = [detector.process(pose("down")) for _ in range(5)]
    results.extend(detector.process(pose("partial")) for _ in range(15))
    assert all(result.state != "UP" for result in results)
    assert results[-1].repetitions == 0
