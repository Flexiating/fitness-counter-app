from app.exercises.exercise_manager import ExerciseManager

from tests.test_crunch import pose as crunch_pose


def test_switching_loads_the_correct_independent_detector() -> None:
    manager = ExerciseManager()
    assert manager.selected_detector_name == "PushUpExercise"

    manager.select("crunch")
    generation, result = manager.process_snapshot(crunch_pose())
    assert generation == manager.generation
    assert manager.selected_detector_name == "CrunchDetector"
    assert "Loaded detector: CrunchDetector" in result.debug
    assert "elbow=" not in result.debug

    manager.select("push_up")
    assert manager.selected_detector_name == "PushUpExercise"


def test_repeated_switching_resets_all_exercise_specific_state() -> None:
    manager = ExerciseManager()
    for _ in range(20):
        manager.select("crunch")
        crunch = manager.selected
        crunch.counter.count = 4
        crunch._signal_ema["Hip angle"] = 100.0

        manager.select("push_up")
        manager.select("crunch")
        crunch = manager.selected
        assert crunch.get_repetitions() == 0
        assert crunch.counter.state.value == "WAITING"
        assert crunch._signal_ema == {}
