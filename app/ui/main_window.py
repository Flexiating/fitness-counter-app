from datetime import datetime
from time import monotonic, sleep
import cv2
from PySide6.QtCore import QCoreApplication, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.camera.camera import Camera
from app.data.storage import WorkoutStorage
from app.data.workout import Workout
from app.exercises.exercise_manager import ExerciseManager
from app.pose.pose_detector import PoseDetector
from app.processing.motion_processor import MotionProcessor
from app.config.settings import SETTINGS
from app.pose.angles import JOINT_ANGLE_TRIPLES, calculate_joint_angles
from app.pose.pose_landmarks import LandmarkName
from app.ui.camera_widget import CameraWidget
from app.ui.widgets import value_label
from app.ui.header import Header
from app.ui.sidebar import Sidebar
from app.ui.stats_panel import StatsPanel
from app.ui.debug_panel import DebugPanel
from app.ui.theme import load_theme
from app.ui.timer_widget import TimerWidget
from app.ui.posture_guide import PostureGuide
from app.ui.translations import translate_debug, translate_exercise, translate_joint, translate_state, translate_status
from app.timer.timer_controller import TimerController
from app.utils.logger import get_logger

log = get_logger(__name__)


class CameraWorker(QThread):
    """Owns the camera loop; it never schedules or calls itself recursively."""
    frame_ready = Signal(QImage)
    result_ready = Signal(int, str, str)
    angles_ready = Signal(dict)
    exercise_debug_ready = Signal(str)
    error = Signal(str)

    def __init__(self, exercise_manager: ExerciseManager) -> None:
        super().__init__()
        self.manager = exercise_manager
        # macOS gives QThread a 544 KB stack by default. MediaPipe's native
        # numerical runtime needs more room than that during inference.
        self.setStackSize(SETTINGS.worker_stack_bytes)
        self._last_frame_at: float | None = None
        self._fps = 0.0

    def run(self) -> None:
        camera, pose_detector, processor = Camera(), PoseDetector(), MotionProcessor()
        try:
            self.result_ready.emit(self.manager.repetitions(), "INITIALIZING", "Opening camera")
            camera.open()
            self.result_ready.emit(self.manager.repetitions(), "INITIALIZING", "Loading pose detector")
            pose_detector.start()
            while not self.isInterruptionRequested():
                frame_started_at = monotonic()
                frame = camera.read()
                if frame is None:
                    if not self.isInterruptionRequested():
                        self.error.emit("Camera frame unavailable. Check the camera connection.")
                    break
                detected = pose_detector.detect(frame)
                fps = self._update_fps()
                if not detected:
                    self._draw(frame, {}, {}, person_detected=False, fps=fps)
                    image = QImage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_RGB888).copy()
                    self.frame_ready.emit(image)
                    self.result_ready.emit(self.manager.repetitions(), "NO PERSON", "No person detected")
                    self.angles_ready.emit({})
                    self.exercise_debug_ready.emit("")
                    self._sleep_to_target(frame_started_at)
                    continue
                landmarks = processor.process(detected)
                result = self.manager.process(landmarks)
                angles = calculate_joint_angles(landmarks)
                self._draw(frame, landmarks, angles, person_detected=True, fps=fps)
                image = QImage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_RGB888).copy()
                self.frame_ready.emit(image)
                self.result_ready.emit(result.repetitions, result.state, result.status)
                self.angles_ready.emit(angles)
                self.exercise_debug_ready.emit(result.debug)
                self._sleep_to_target(frame_started_at)
        except Exception as exc:
            log.exception("Camera worker failed")
            self.error.emit(str(exc))
        finally:
            camera.release()
            pose_detector.close()

    @staticmethod
    def _sleep_to_target(frame_started_at: float) -> None:
        remaining = (1 / SETTINGS.target_fps) - (monotonic() - frame_started_at)
        if remaining > 0:
            sleep(remaining)

    def _update_fps(self) -> float:
        now = monotonic()
        if self._last_frame_at is not None:
            instantaneous = 1 / max(now - self._last_frame_at, 0.001)
            self._fps = instantaneous if self._fps == 0 else (0.2 * instantaneous + 0.8 * self._fps)
        self._last_frame_at = now
        return self._fps

    def _draw(self, frame, landmarks, angles, person_detected: bool = True, fps: float = 0.0) -> None:
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
        confidence = sum(point.visibility for point in landmarks.values()) / len(landmarks) if landmarks else 0.0
        lines = [
            f"Người: {'đã phát hiện' if person_detected else 'chưa phát hiện'}",
            f"FPS: {fps:.1f}",
            f"Độ tin cậy: {confidence:.0%}",
        ]
        for index, text in enumerate(lines):
            cv2.putText(frame, text, (16, 30 + index * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)
        for name, value in angles.items():
            if name not in JOINT_ANGLE_TRIPLES:
                continue
            _, joint, _ = JOINT_ANGLE_TRIPLES[name]
            point = landmarks[joint]
            cv2.putText(frame, f"{value:.0f}°", (int(point.x * width) + 6, int(point.y * height) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (253, 224, 71), 2)

    def stop(self) -> None:
        self.requestInterruption()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.manager = ExerciseManager()
        self.storage, self.started_at = WorkoutStorage(), None
        self.worker = None
        self.timer=TimerController(); self.timer_enabled=True; self._last_reps=0; self.timer.changed.connect(self._timer_changed); self.timer.finished.connect(self._timer_finished)
        self._retired_workers: list[CameraWorker] = []
        self.setWindowTitle("Bộ đếm bài tập")
        self.resize(1280, 800)
        self.setStyleSheet(load_theme())
        self._build()

    def _build(self) -> None:
        root = QWidget(); layout = QVBoxLayout(root); layout.setSpacing(14); header=Header(); layout.addWidget(header); self.timer_card=TimerWidget(); layout.addWidget(self.timer_card)
        body=QHBoxLayout(); self.sidebar=Sidebar(self.manager.names); self.selector=self.sidebar.selector; self.selector.currentIndexChanged.connect(self._change_exercise)
        self.start_button=self.sidebar.start; self.stop_button=self.sidebar.stop; self.stop_button.setEnabled(False); self.start_button.clicked.connect(self.start); self.stop_button.clicked.connect(self.stop_camera); self.sidebar.reset.clicked.connect(self.reset)
        self.sidebar.timer_enabled.toggled.connect(self._set_timer_enabled); self.sidebar.apply_timer.clicked.connect(self._apply_timer_settings)
        body.addWidget(self.sidebar,1); center=QVBoxLayout(); self.camera_view=CameraWidget(); self.camera_view.setStyleSheet("background:#020617;border:2px solid #3B82F6;border-radius:16px;"); center.addWidget(self.camera_view,1)
        self.count_caption=QLabel("Chống đẩy:"); self.reps=value_label("0",72); self.person=value_label("Người: chưa phát hiện",16); self.state=value_label("Trạng thái: Đang khởi tạo...",18)
        for widget in (self.count_caption,self.reps,self.person,self.state): center.addWidget(widget)
        self.posture_guide=PostureGuide(); center.addWidget(self.posture_guide); body.addLayout(center,4); self.debug_drawer=DebugPanel(); self.debug_drawer.setVisible(False); body.addWidget(self.debug_drawer,1); layout.addLayout(body,1)
        self.stats=StatsPanel(); layout.addWidget(self.stats)
        self.angle_debug=self.debug_drawer.content; self.exercise_debug=self.debug_drawer.content
        self.setCentralWidget(root)

    @Slot()
    def start(self) -> None:
        if self.worker is not None: return
        self.started_at = datetime.now(); self.start_button.setEnabled(False); self.stop_button.setEnabled(True); self.selector.setEnabled(False)
        self.worker = CameraWorker(self.manager)
        self._retired_workers.append(self.worker)
        self.worker.frame_ready.connect(self.camera_view.set_frame); self.worker.result_ready.connect(self.update_result)
        self.worker.angles_ready.connect(self.update_angles)
        self.worker.exercise_debug_ready.connect(self.update_exercise_debug)
        self.worker.error.connect(self.show_error); self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    @Slot()
    def stop_camera(self) -> None:
        worker = self.worker
        if worker is None:
            return
        self.state.setText("Trạng thái: Đang tắt camera...")
        self.stop_button.setEnabled(False)
        worker.stop()
        worker.quit()
        QCoreApplication.processEvents()
        if not worker.wait(1_500):
            self.state.setText("Trạng thái: Đang chờ camera tắt...")
            return
        self._finalize_worker(worker)

    @Slot(int, str, str)
    def update_result(self, repetitions: int, state: str, status: str) -> None:
        self.reps.setText(str(repetitions)); self.state.setText(f"Trạng thái: {translate_state(state)} — {translate_status(status)}")
        self.person.setText("Người: chưa phát hiện" if state == "NO PERSON" else "Người: đã phát hiện")
        if self.timer_enabled and repetitions > self._last_reps: self.timer.start_on_rep()
        self._last_reps = repetitions

    def _timer_changed(self, state: str, value: str) -> None:
        self.timer_card.value.setText(value if state != "READY" else "SẴN SÀNG")

    def _set_timer_enabled(self, enabled: bool) -> None:
        self.timer_enabled=enabled; self.timer_card.setVisible(enabled)
        if not enabled: self.timer.reset()

    def _apply_timer_settings(self) -> None:
        self.timer.configure(str(self.sidebar.timer_mode.currentData()), int(self.sidebar.timer_duration.currentData()))

    def _timer_finished(self, duration: float) -> None:
        self.stop_camera(); QMessageBox.information(self, "Hoàn thành buổi tập", f"Buổi tập đã hoàn thành\nThời gian: {int(duration)} giây\nSố lần: {self.reps.text()}")

    @Slot(dict)
    def update_angles(self, angles: dict) -> None:
        if not angles:
            self.angle_debug.setText("Góc khớp: chưa phát hiện tư thế")
            return
        values = "   ".join(f"{translate_joint(name)}: {value:.0f}°" for name, value in angles.items())
        self.angle_debug.setText(f"Góc khớp\n{values}")

    @Slot(str)
    def update_exercise_debug(self, debug: str) -> None:
        self.exercise_debug.setText(translate_debug(debug) if debug else "Gỡ lỗi chống đẩy: chưa phát hiện tư thế")

    @Slot()
    def reset(self) -> None:
        self.manager.reset(); self.reps.setText("0"); self.state.setText("Trạng thái: Sẵn sàng"); self._last_reps=0; self.timer.reset()

    @Slot(int)
    def _change_exercise(self, _index: int) -> None:
        self.manager.select(str(self.selector.currentData())); self.reset()
        self.count_caption.setText("Chống đẩy:" if self.selector.currentData() == "push_up" else f"{translate_exercise(self.manager.selected.name)}:")
        self.posture_guide.set_exercise(str(self.selector.currentData()))

    @Slot(str)
    def show_error(self, message: str) -> None:
        translated = translate_status(message)
        self.state.setText(f"Trạng thái: {translated}")
        QMessageBox.warning(self, "Bộ đếm bài tập", translated)

    @Slot()
    def _on_worker_finished(self) -> None:
        worker = self.sender()
        if isinstance(worker, CameraWorker):
            self._finalize_worker(worker)

    def _finalize_worker(self, worker: CameraWorker) -> None:
        """Keep the QThread alive until it has fully returned from run()."""
        if worker.isRunning():
            QTimer.singleShot(10, lambda: self._finalize_worker(worker))
            return
        if not any(item is worker for item in self._retired_workers):
            return
        worker.wait()
        self._retired_workers.remove(worker)
        if self.worker is worker:
            self.worker = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.selector.setEnabled(True)
            self.state.setText("Trạng thái: Camera đã tắt")
        worker.deleteLater()

    def closeEvent(self, event) -> None:
        if self.worker:
            self.stop_camera()
            if self.worker:
                event.ignore()
                return
        repetitions = self.manager.repetitions()
        if self.started_at and repetitions:
            self.storage.append(Workout.create(self.manager.selected.name, repetitions, self.started_at, datetime.now()))
        event.accept()
