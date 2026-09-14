import numpy as np

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from app.exercises.exercise_manager import ExerciseManager
from app.config.settings import SETTINGS
from app.ui.main_window import CameraWorker


def test_camera_worker_runs_once_and_quits_its_thread(monkeypatch) -> None:
    """Exercise the production QThread wiring without a physical camera."""
    class FakeCamera:
        def open(self): pass
        def read(self): return None
        def release(self): pass

    class FakePoseDetector:
        def start(self): raise AssertionError("Detector should not start without a frame")
        def detect(self, _frame): raise AssertionError("Detector should not process without a frame")
        def close(self): pass

    monkeypatch.setattr("app.ui.main_window.Camera", FakeCamera)
    monkeypatch.setattr("app.ui.main_window.PoseDetector", FakePoseDetector)
    application = QCoreApplication.instance() or QCoreApplication([])
    loop, worker = QEventLoop(), CameraWorker(ExerciseManager())
    assert worker.stackSize() == SETTINGS.worker_stack_bytes
    worker.finished.connect(loop.quit)
    QTimer.singleShot(2_000, loop.quit)
    worker.start()
    loop.exec()

    assert not worker.isRunning()
    worker.deleteLater()
