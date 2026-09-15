from app.exercise.crunch_counter import CrunchCounter, CrunchState


def angles(stage: str = "down"):
    if stage == "up":
        return {
            "Hip angle": 100.0,
            "Torso flexion": 80.0,
            "Torso angle": 48.0,
            "Shoulder lift": .75,
            "Lower body angle": 10.0,
            "Body rotation": 5.0,
            "Body size": .52,
            "Whole body inside": 1.0,
            "Neck angle": 165.0,
            "Shoulder-hip ratio": .68,
            "Nose-knee ratio": .74,
        }
    if stage == "partial":
        return {
            "Hip angle": 128.0,
            "Torso flexion": 52.0,
            "Torso angle": 20.0,
            "Shoulder lift": .30,
            "Lower body angle": 10.0,
            "Body rotation": 5.0,
            "Body size": .52,
            "Whole body inside": 1.0,
            "Neck angle": 165.0,
            "Shoulder-hip ratio": .94,
            "Nose-knee ratio": .96,
        }
    return {
        "Hip angle": 145.0,
        "Torso flexion": 35.0,
        "Torso angle": 5.0,
        "Shoulder lift": .10,
        "Lower body angle": 10.0,
        "Body rotation": 5.0,
        "Body size": .55,
        "Whole body inside": 1.0,
        "Neck angle": 170.0,
        "Shoulder-hip ratio": 1.0,
        "Nose-knee ratio": 1.0,
    }


def coords(hip=(.55, .70)):
    return {"selected_hip": hip}


def visible(value=.9):
    return {
        f"selected_{joint}": value
        for joint in ("head", "shoulder", "hip", "knee", "ankle")
    }


def settle(counter, stage, start):
    counter.update(angles(stage), coords(), visible(), start)
    return counter.update(angles(stage), coords(), visible(), start + .21)


def test_crunch_has_dedicated_down_up_down_state_machine() -> None:
    counter = CrunchCounter()
    assert counter.update(angles("down"), coords(), visible(), 0).state is CrunchState.READY
    assert counter.update(angles("down"), coords(), visible(), .21).state is CrunchState.DOWN
    assert counter.update(angles("up"), coords(), visible(), .35).state is CrunchState.DOWN
    assert counter.update(angles("up"), coords(), visible(), .56).state is CrunchState.UP
    assert counter.count == 0
    counter.update(angles("down"), coords(), visible(), .75)
    result = counter.update(angles("down"), coords(), visible(), .96)
    assert result.state is CrunchState.DOWN
    assert result.count == 1


def test_ten_slow_crunches_count_independently() -> None:
    counter = CrunchCounter()
    counter.update(angles("down"), coords(), visible(), 0)
    counter.update(angles("down"), coords(), visible(), .21)
    timestamp = .35
    for _ in range(10):
        counter.update(angles("up"), coords(), visible(), timestamp)
        counter.update(angles("up"), coords(), visible(), timestamp + .21)
        counter.update(angles("down"), coords(), visible(), timestamp + .45)
        result = counter.update(angles("down"), coords(), visible(), timestamp + .66)
        timestamp += .80
    assert result.count == 10


def test_partial_crunch_and_standing_are_ignored() -> None:
    counter = CrunchCounter()
    counter.update(angles("down"), coords(), visible(), 0)
    counter.update(angles("down"), coords(), visible(), .21)
    for timestamp in (.4, .7, 1.0):
        result = counter.update(angles("partial"), coords(), visible(), timestamp)
    assert result.count == 0
    standing = dict(angles("down"))
    standing["Lower body angle"] = 88.0
    result = counter.update(standing, coords(), visible(), 1.4)
    assert result.posture_valid is False
    assert "Standing" in result.feedback


def test_crunch_feedback_uses_neck_and_lower_back_rules() -> None:
    counter = CrunchCounter()
    counter.update(angles("down"), coords(), visible(), 0)
    counter.update(angles("down"), coords(), visible(), .21)
    bad_neck = dict(angles("partial"))
    bad_neck["Neck angle"] = 120.0
    assert "neck" in counter.update(bad_neck, coords(), visible(), .5).feedback

    counter.update(angles("up"), coords(), visible(), .8)
    counter.update(angles("up"), coords(), visible(), 1.01)
    shifted = counter.update(angles("partial"), coords((.70, .70)), visible(), 1.3)
    assert "lower back" in shifted.feedback


def test_debug_identifies_the_loaded_crunch_detector() -> None:
    result = CrunchCounter().update(angles("down"), coords(), visible(), 0)
    assert "Exercise: Crunch" in result.debug_info
    assert "Loaded detector: CrunchDetector" in result.debug_info
    assert "State machine: CrunchStateMachine" in result.debug_info
