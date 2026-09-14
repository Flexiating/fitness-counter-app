from app.exercise.pushup_counter import PushUpCounter, PushUpState


def angles(elbow: float, hip: float = 170.0, orientation: float = 0.0):
    return {"Left elbow": elbow, "Right elbow": elbow, "Left hip": hip, "Right hip": hip, "Body orientation": orientation}


def visibility():
    return {name: 1.0 for name in ("left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip")}


def test_slow_complete_push_up_counts_on_return_to_up() -> None:
    counter = PushUpCounter()
    assert counter.update(angles(170), visibility(), 0).state is PushUpState.UP
    assert counter.update(angles(60), visibility(), .3).state is PushUpState.DOWN
    result = counter.update(angles(170), visibility(), .6)
    assert result.repetitions == 1 and result.state is PushUpState.UP


def test_fast_oscillation_and_partial_movement_do_not_count() -> None:
    counter = PushUpCounter()
    counter.update(angles(170), visibility(), 0)
    counter.update(angles(60), visibility(), .05)
    assert counter.update(angles(170), visibility(), .1).repetitions == 0
    assert counter.update(angles(120), visibility(), .5).repetitions == 0


def test_standing_or_incomplete_body_and_bad_hips_are_rejected() -> None:
    counter = PushUpCounter()
    missing_arm = dict(angles(170)); missing_arm.pop("Right elbow")
    assert counter.update(missing_arm, visibility(), 0).posture == "BAD"
    assert counter.update(angles(170, 110), visibility(), .3).reason == "Hips too high or too low"
    assert counter.update(angles(170, orientation=90), visibility(), .5).reason == "Not in plank position (standing or walking)"
    hidden = visibility(); hidden["left_wrist"] = .1
    assert counter.update(angles(170), hidden, .6).posture == "BAD"
