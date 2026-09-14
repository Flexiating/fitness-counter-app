from datetime import datetime
from time import monotonic, sleep

import cv2
from PySide6.QtCore import QThread, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.camera.camera import Camera
from app.data.storage import WorkoutStorage
from app.data.workout import Workout
from app.exercises.exercise_manager import ExerciseManager
from app.models.model_manager import ModelManager
from app.processing.motion_processor import MotionProcessor
from app.config.settings import SETTINGS
from app.pose.pose_landmarks import LandmarkName
from app.ui.camera_widget import CameraWidget
from app.ui.widgets import value_label
from app.utils.logger import get_logger

log = get_logger(__name__)


class CameraWorker(QThread):
    """Owns the camera loop; it never schedules or calls itself recursively."""
    frame_ready = Signal(QImage)
    result_ready = Signal(int, str, str)
    error = Signal(str)

    def __init__(self, exercise_manager: ExerciseManager) -> None:
        super().__init__()
        self.manager = exercise_manager
        # macOS gives QThread a 544 KB stack by default. MediaPipe's native
        # numerical runtime needs more room than that during inference.
        self.setStackSize(SETTINGS.worker_stack_bytes)

    def run(self) -> None:
        camera, model_manager, processor = Camera(), ModelManager(), MotionProcessor()
        try:
            self.result_ready.emit(self.manager.repetitions(), "INITIALIZING", "Opening camera")
            camera.open()
            self.result_ready.emit(self.manager.repetitions(), "INITIALIZING", "Loading pose detector")
            model = model_manager.start()
            while not self.isInterruptionRequested():
                frame_started_at = monotonic()
                frame = camera.read()
                if frame is None:
                    self.error.emit("Camera frame unavailable. Check the camera connection.")
                    break
                detected = model.predict(frame)
                if not detected:
                    self._draw(frame, {}, {})
                    image = QImage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_RGB888).copy()
                    self.frame_ready.emit(image)
                    self.result_ready.emit(self.manager.repetitions(), "NO PERSON", "No person detected")
                    self._sleep_to_target(frame_started_at)
                    continue
                landmarks = processor.process(detected)
                result = self.manager.process(landmarks)
                self._draw(frame, landmarks, result.angles)
                image = QImage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_RGB888).copy()
                self.frame_ready.emit(image)
                self.result_ready.emit(result.repetitions, result.state, result.status)
                self._sleep_to_target(frame_started_at)
        except Exception as exc:
            log.exception("Camera worker failed")
            self.error.emit(str(exc))
        finally:
            camera.release()
            model_manager.close()

    @staticmethod
    def _sleep_to_target(frame_started_at: float) -> None:
        remaining = (1 / SETTINGS.target_fps) - (monotonic() - frame_started_at)
        if remaining > 0:
            sleep(remaining)

    def _draw(self, frame, landmarks, angles) -> None:
        height, width = frame.shape[:2]
        connections = (
            ("LEFT_SHOULDER", "RIGHT_SHOULDER"), ("LEFT_SHOULDER", "LEFT_ELBOW"),
            ("LEFT_ELBOW", "LEFT_WRIST"), ("RIGHT_SHOULDER", "RIGHT_ELBOW"),
            ("RIGHT_ELBOW", "RIGHT_WRIST"), ("LEFT_SHOULDER", "LEFT_HIP"),
            ("RIGHT_SHOULDER", "RIGHT_HIP"), ("LEFT_HIP", "RIGHT_HIP"),
            ("LEFT_HIP", "LEFT_KNEE"), ("LEFT_KNEE", "LEFT_ANKLE"),
            ("RIGHT_HIP", "RIGHT_KNEE"), ("RIGHT_KNEE", "RIGHT_ANKLE"),
        )
        for first, second in connections:
            a, b = LandmarkName[first], LandmarkName[second]
            if a in landmarks and b in landmarks and landmarks[a].visibility > 0.4 and landmarks[b].visibility > 0.4:
                cv2.line(frame, (int(landmarks[a].x * width), int(landmarks[a].y * height)), (int(landmarks[b].x * width), int(landmarks[b].y * height)), (34, 197, 94), 2)
        for point in landmarks.values():
            if point.visibility > 0.4:
                cv2.circle(frame, (int(point.x * width), int(point.y * height)), 4, (56, 189, 248), -1)
        if angles:
            cv2.putText(frame, "  ".join(f"{name}: {value:.0f}" for name, value in angles.items()), (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def stop(self) -> None:
        self.requestInterruption()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.manager = ExerciseManager()
        self.storage, self.started_at = WorkoutStorage(), None
        self.worker = None
        self.setWindowTitle("Fitness Counter")
        self.resize(960, 760)
        self._build()

    def _build(self) -> None:
        root = QWidget(); layout = QVBoxLayout(root); layout.setSpacing(14)
        title = value_label("FITNESS COUNTER", 28); layout.addWidget(title)
        self.camera_view = CameraWidget(); layout.addWidget(self.camera_view, 1)
        controls = QHBoxLayout(); controls.addWidget(QLabel("Exercise:"))
        self.selector = QComboBox()
        for key, name in self.manager.names.items(): self.selector.addItem(name, key)
        self.selector.currentIndexChanged.connect(self._change_exercise); controls.addWidget(self.selector)
        controls.addStretch(); controls.addWidget(QLabel("Repetitions:")); self.reps = value_label("0", 34); controls.addWidget(self.reps)
        layout.addLayout(controls)
        self.state = value_label("State: Initializing...", 18); layout.addWidget(self.state)
        buttons = QHBoxLayout(); self.start_button = QPushButton("Start"); self.start_button.clicked.connect(self.start)
        reset = QPushButton("Reset"); reset.clicked.connect(self.reset); buttons.addWidget(self.start_button); buttons.addWidget(reset); buttons.addStretch(); layout.addLayout(buttons)
        self.setCentralWidget(root)
        self.setStyleSheet("QMainWindow { background:#0f172a; color:#e2e8f0; } QPushButton,QComboBox { padding:8px 14px; background:#2563eb; color:white; border-radius:6px; }")

    @Slot()
    def start(self) -> None:
        if self.worker is not None: return
        self.started_at = datetime.now(); self.start_button.setEnabled(False); self.selector.setEnabled(False)
        self.worker = CameraWorker(self.manager)
        self.worker.frame_ready.connect(self.camera_view.set_frame); self.worker.result_ready.connect(self.update_result)
        self.worker.error.connect(self.show_error); self.worker.finished.connect(self._stopped); self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    @Slot(int, str, str)
    def update_result(self, repetitions: int, state: str, status: str) -> None:
        self.reps.setText(str(repetitions)); self.state.setText(f"State: {state} — {status}")

    @Slot()
    def reset(self) -> None:
        self.manager.reset(); self.reps.setText("0"); self.state.setText("State: Ready")

    @Slot(int)
    def _change_exercise(self, _index: int) -> None:
        self.manager.select(str(self.selector.currentData())); self.reset()

    @Slot(str)
    def show_error(self, message: str) -> None:
        self.state.setText(f"State: {message}")
        QMessageBox.warning(self, "Fitness Counter", message)

    @Slot()
    def _stopped(self) -> None:
        self.worker = None; self.start_button.setEnabled(True); self.selector.setEnabled(True)

    def closeEvent(self, event) -> None:
        if self.worker: self.worker.stop()
        repetitions = self.manager.repetitions()
        if self.started_at and repetitions:
            self.storage.append(Workout.create(self.manager.selected.name, repetitions, self.started_at, datetime.now()))
        event.accept()
