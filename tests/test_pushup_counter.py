from app.exercise.pushup_counter import PushUpCounter, PushUpState


def angles(
    elbow: float,
    hip: float = 170.0,
    orientation: float = 0.0,
    body_size: float = .55,
    form_score: float = 90.0,
):
    return {
        "Selected elbow": elbow,
        "Selected hip": hip,
        "Body orientation": orientation,
        "Back alignment": hip,
        "Body size": body_size,
        "Whole body inside": 1.0,
        "Form score": form_score,
    }


def visibility(value: float = .9):
    return {
        f"selected_{joint}": value
        for joint in ("shoulder", "elbow", "wrist", "hip", "knee", "ankle")
    }


def test_complete_push_up_uses_ready_and_counts_only_on_down_to_up() -> None:
    counter = PushUpCounter()
    assert counter.update(angles(165), visibility(), 0).state is PushUpState.READY
    assert counter.update(angles(165), visibility(), .21).state is PushUpState.UP
    assert counter.update(angles(88), visibility(), .30).state is PushUpState.UP
    assert counter.update(angles(88), visibility(), .51).state is PushUpState.DOWN
    assert counter.update(angles(155), visibility(), .60).repetitions == 0
    result = counter.update(angles(155), visibility(), .81)
    assert result.repetitions == 1
    assert result.state is PushUpState.UP


def test_single_frame_oscillation_and_partial_movement_do_not_count() -> None:
    counter = PushUpCounter()
    counter.update(angles(165), visibility(), 0)
    counter.update(angles(165), visibility(), .21)
    counter.update(angles(88), visibility(), .30)
    counter.update(angles(165), visibility(), .35)
    counter.update(angles(120), visibility(), .70)
    assert counter.repetitions == 0
    assert counter.state is PushUpState.UP


def test_best_visible_side_is_enough_but_bad_body_alignment_is_rejected() -> None:
    counter = PushUpCounter()
    bilateral_angles = {
        "Left elbow": 165.0,
        "Left hip": 165.0,
        "Body orientation": 0.0,
    }
    bilateral_visibility = {
        "left_shoulder": .9,
        "left_elbow": .9,
        "left_wrist": .9,
        "left_hip": .9,
        "right_shoulder": .1,
        "right_elbow": .1,
        "right_wrist": .1,
        "right_hip": .1,
    }
    assert counter.update(bilateral_angles, bilateral_visibility, 0).posture == "GOOD"
    assert counter.update(angles(165, hip=120), visibility(), .3).reason == "Hips too high or too low"
    assert "standing" in counter.update(angles(165, orientation=70), visibility(), .6).reason


def test_body_distance_and_weak_selected_landmark_have_clear_reasons() -> None:
    counter = PushUpCounter()
    assert "28%" in counter.update(angles(165, body_size=.28), visibility(), 0).reason
    hidden = visibility()
    hidden["selected_wrist"] = .1
    assert "Wrist visibility" in counter.update(angles(165), hidden, .3).reason


def test_sustained_invalid_posture_resets_motion_without_losing_reps() -> None:
    counter = PushUpCounter()
    counter.update(angles(165), visibility(), 0)
    counter.update(angles(165), visibility(), .21)
    counter.repetitions = 3
    counter.update(angles(165, orientation=70), visibility(), .30)
    result = counter.update(angles(165, orientation=70), visibility(), 1.06)
    assert result.state is PushUpState.WAITING
    assert result.repetitions == 3
