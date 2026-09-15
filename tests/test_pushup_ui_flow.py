from app.ui.main_window import MainWindow


def test_ui_displays_completed_pushup_from_worker_result() -> None:
    window = MainWindow()
    generation = window._exercise_generation

    window.update_result(0, "UP", "Posture: GOOD", generation)
    window.update_result(1, "UP", "Posture: GOOD", generation)

    assert window.reps.text() == "1"
    assert window.metrics.repetitions == 1
    window.close()


def test_ui_uses_weighted_pushup_form_score() -> None:
    score, grade, _color, valid = MainWindow._quality_for_status(
        35.0,
        "Posture: GOOD — Form score: 88%",
        "UP",
    )
    assert score == 88.0
    assert grade == "Tốt"
    assert valid is True
