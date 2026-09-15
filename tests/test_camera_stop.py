import numpy as np

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from app.exercises.exercise_manager import ExerciseManager
from app.ui.main_window import CameraWorker


def test_worker_can_stop_and_restart_one_hundred_times(monkeypatch) -> None:
    releases = []
    closes = []

    class FakeCamera:
        def open(self): pass
        def read(self): return np.zeros((32, 32, 3), dtype=np.uint8)
        def release(self): releases.append(True)

    class FakePoseDetector:
        def start(self): pass
        def detect(self, _frame): return {}
        def close(self): closes.append(True)

    monkeypatch.setattr("app.ui.main_window.Camera", FakeCamera)
    monkeypatch.setattr("app.ui.main_window.PoseDetector", FakePoseDetector)
    QCoreApplication.instance() or QCoreApplication([])

    for _ in range(100):
        loop, worker = QEventLoop(), CameraWorker(ExerciseManager())
        worker.finished.connect(loop.quit)
        worker.start()
        QTimer.singleShot(10, worker.stop)
        QTimer.singleShot(2_000, loop.quit)
        loop.exec()
        assert not worker.isRunning()

    assert len(releases) == 100
    assert len(closes) == 100
