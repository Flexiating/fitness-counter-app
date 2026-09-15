from PySide6.QtGui import QImage

from app.ui.camera_widget import CameraWidget
from app.ui.main_window import CameraWorker, MainWindow
from app.ui.workout_metrics import LiveWorkoutMetrics


def test_camera_hud_countdown_and_stopped_state() -> None:
    widget = CameraWidget()
    image = QImage(64, 48, QImage.Format.Format_RGB888)
    image.fill(0)
    widget.show_starting()
    widget.set_frame(image)
    widget.set_hud("Chống đẩy", "LÊN", 4, "00:12", 30.0, 96.0, 94.0)
    widget.show_countdown("3")

    assert "4 lần" in widget.hud_info.text()
    assert "30 FPS" in widget.hud_metrics.text()
    assert "00:12" in widget.hud_timer.text()
    assert widget.countdown.text() == "3"
    widget.show_stopped()
    assert widget.pixmap().isNull()
    assert not widget.hud_info.isVisible()
    assert not widget.hud_timer.isVisible()
    assert "Camera Stopped" in widget.text()


def test_live_workout_metrics_tracks_speed_and_quality() -> None:
    metrics = LiveWorkoutMetrics()
    metrics.update_quality(95, True)
    metrics.record_repetitions(1, 10.0)
    metrics.update_quality(85, True)
    metrics.record_repetitions(1, 12.0)
    snapshot = metrics.snapshot(12.0)

    assert snapshot.repetitions == 2
    assert snapshot.current_rep_seconds == 2.0
    assert snapshot.average_rep_seconds == 2.0
    assert snapshot.reps_per_minute == 10.0
    assert snapshot.accuracy == 100.0
    assert snapshot.best_streak == 2


def test_dashboard_exposes_goals_tabs_and_shortcuts() -> None:
    window = MainWindow()
    window.sidebar.target_reps.setValue(10)
    window.sidebar.target_sets.setValue(2)
    window._goals_changed(10, 2)

    assert window.tabs.count() == 4
    assert window.tabs.tabText(2) == "Hướng dẫn"
    assert len(window._shortcuts) == 4
    assert window.workout_status.goal_progress.maximum() == 10
    assert "10" in window.workout_status.goal_value.text()
    window.close()


def test_skeleton_posture_palette() -> None:
    assert CameraWorker._skeleton_color("Posture: GOOD", True) == (94, 197, 34)
    assert CameraWorker._skeleton_color("Partial crunch ignored", True) == (11, 158, 245)
    assert CameraWorker._skeleton_color("Posture: BAD", True) == (68, 68, 239)
    assert CameraWorker._skeleton_color("", False) == (148, 148, 148)
