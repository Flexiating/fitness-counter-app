from __future__ import annotations

import subprocess
import sys
from time import monotonic

import numpy as np
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QImage

from app.data.history import HistoryRepository
from app.ui.translations import tr
from app.timer.session_timer import TimerState
from app.timer.timer_controller import TimerController
from app.ui.camera_widget import CameraWidget
from app.ui.main_window import MainWindow


class FakeCamera:
    releases = 0

    def open(self) -> None:
        pass

    def read(self):
        return np.zeros((32, 48, 3), dtype=np.uint8)

    def release(self) -> None:
        type(self).releases += 1


class FakePoseDetector:
    closes = 0

    def start(self) -> None:
        pass

    def detect(self, _frame):
        return {}

    def close(self) -> None:
        type(self).closes += 1


def finish_worker(window: MainWindow) -> None:
    worker = window.worker
    if worker is None:
        return
    loop = QEventLoop()
    worker.finished.connect(loop.quit)
    if not worker.isRunning():
        QTimer.singleShot(0, loop.quit)
    QTimer.singleShot(2_000, loop.quit)
    loop.exec()


def test_stop_is_non_blocking_and_clears_preview(monkeypatch) -> None:
    monkeypatch.setattr("app.ui.main_window.Camera", FakeCamera)
    monkeypatch.setattr("app.ui.main_window.PoseDetector", FakePoseDetector)
    window = MainWindow()
    window.start()
    started = monotonic()
    window.stop_camera()
    elapsed = monotonic() - started

    assert elapsed < 0.1
    assert tr("camera.stopped") in window.camera_view.text()
    assert window.camera_view.pixmap().isNull()
    finish_worker(window)
    assert window.worker is None
    window.close()


def test_exercise_switch_keeps_worker_and_enters_ready(monkeypatch) -> None:
    monkeypatch.setattr("app.ui.main_window.Camera", FakeCamera)
    monkeypatch.setattr("app.ui.main_window.PoseDetector", FakePoseDetector)
    window = MainWindow()
    window.start()
    worker = window.worker
    started = monotonic()
    window.selector.setCurrentIndex(window.selector.findData("crunch"))
    elapsed = monotonic() - started

    assert elapsed < 0.1
    assert window.worker is worker
    assert window.selector.isEnabled()
    assert window.timer.state is TimerState.READY
    assert window.reps.text() == "0"
    assert "Sẵn sàng" in window.state.text()
    window.stop_camera()
    finish_worker(window)
    window.close()


def test_main_window_releases_one_hundred_workers(monkeypatch) -> None:
    FakeCamera.releases = 0
    FakePoseDetector.closes = 0
    monkeypatch.setattr("app.ui.main_window.Camera", FakeCamera)
    monkeypatch.setattr("app.ui.main_window.PoseDetector", FakePoseDetector)
    window = MainWindow()

    for _ in range(100):
        window.start()
        window.stop_camera()
        finish_worker(window)
        assert window.worker is None
        assert window._retired_workers == []

    assert FakeCamera.releases == 100
    assert FakePoseDetector.closes == 100
    window.close()


def test_stopped_camera_rejects_queued_stale_frames() -> None:
    widget = CameraWidget()
    image = QImage(16, 16, QImage.Format.Format_RGB888)
    image.fill(0xFFFFFF)
    widget.show_starting()
    widget.set_frame(image)
    assert not widget.pixmap().isNull()
    widget.show_stopped()
    widget.set_frame(image)
    assert widget.pixmap().isNull()
    assert tr("camera.stopped") in widget.text()


def test_ui_import_does_not_eagerly_import_native_vision_libraries() -> None:
    check = (
        "import sys; import app.ui.main_window; "
        "assert 'cv2' not in sys.modules; assert 'mediapipe' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", check], check=True)


def test_countdown_and_pause_transitions(monkeypatch) -> None:
    clock = [0.0]
    monkeypatch.setattr("app.timer.timer_controller.monotonic", lambda: clock[0])
    timer = TimerController()
    timer.configure("countdown", 1)
    finished = []
    timer.finished.connect(finished.append)
    timer.start_on_rep()
    clock[0] = 0.4
    timer.pause()
    assert timer.state is TimerState.PAUSED
    clock[0] = 0.8
    timer.resume()
    clock[0] = 1.5
    timer._update()
    assert timer.state is TimerState.FINISHED
    assert finished == [1.0]


def test_history_uses_sqlite_storage(tmp_path) -> None:
    storage = HistoryRepository(tmp_path / "history.sqlite3")
    assert storage.list() == []
