from datetime import datetime
from threading import Event
from time import monotonic, sleep
from PySide6.QtCore import QThread, Signal, Slot, QTimer, Qt
from PySide6.QtGui import QImage, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.camera.camera import Camera
from app.data.storage import WorkoutStorage
from app.data.workout import Workout
from app.exercises.exercise_manager import ExerciseManager
from app.pose.pose_detector import PoseDetector
from app.processing.motion_processor import MotionProcessor
from app.session.session_manager import SessionManager
from app.config.settings import SETTINGS
from app.pose.angles import JOINT_ANGLE_TRIPLES
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
from app.ui.summary_dialog import WorkoutSummaryDialog
from app.ui.translations import translate_exercise, translate_state, translate_status
from app.ui.workout_metrics import LiveWorkoutMetrics, speed_label
from app.ui.workout_status import WorkoutStatusPanel
from app.timer.timer_controller import TimerController
from app.timer.session_timer import TimerState
from app.utils.logger import get_logger

log = get_logger(__name__)


class CameraWorker(QThread):
    """Owns the camera loop; it never schedules or calls itself recursively."""
    frame_ready = Signal(QImage)
    result_ready = Signal(int, str, str, int)
    angles_ready = Signal(dict, int)
    exercise_debug_ready = Signal(str, int)
    telemetry_ready = Signal(float, float, int)
    error = Signal(str)

    _CONNECTIONS = tuple(
        (LandmarkName[first], LandmarkName[second])
        for first, second in (
            ("LEFT_SHOULDER", "RIGHT_SHOULDER"), ("LEFT_SHOULDER", "LEFT_ELBOW"),
            ("LEFT_ELBOW", "LEFT_WRIST"), ("RIGHT_SHOULDER", "RIGHT_ELBOW"),
            ("RIGHT_ELBOW", "RIGHT_WRIST"), ("LEFT_SHOULDER", "LEFT_HIP"),
            ("RIGHT_SHOULDER", "RIGHT_HIP"), ("LEFT_HIP", "RIGHT_HIP"),
            ("LEFT_HIP", "LEFT_KNEE"), ("LEFT_KNEE", "LEFT_ANKLE"),
            ("RIGHT_HIP", "RIGHT_KNEE"), ("RIGHT_KNEE", "RIGHT_ANKLE"),
        )
    )
    _cv2 = None

    def __init__(self, exercise_manager: ExerciseManager) -> None:
        super().__init__()
        self.manager = exercise_manager
        # macOS gives QThread a 544 KB stack by default. MediaPipe's native
        # numerical runtime needs more room than that during inference.
        self.setStackSize(SETTINGS.worker_stack_bytes)
        self._last_frame_at: float | None = None
        self._fps = 0.0
        self._last_result: tuple[int, str, str, int] | None = None
        self._last_debug_at = 0.0
        self._last_telemetry_at = 0.0
        self._frame_pending = Event()

    def run(self) -> None:
        cv2 = self._opencv()
        camera, pose_detector, processor = Camera(), PoseDetector(), MotionProcessor()
        phase = "camera"
        try:
            if self.isInterruptionRequested():
                return
            generation = self.manager.generation
            self._emit_result(self.manager.repetitions(), "INITIALIZING", "Opening camera", generation)
            camera.open()
            if self.isInterruptionRequested():
                return
            phase = "model"
            generation = self.manager.generation
            self._emit_result(self.manager.repetitions(), "INITIALIZING", "Loading pose detector", generation)
            pose_detector.start()
            if self.isInterruptionRequested():
                return
            phase = "processing"
            generation = self.manager.generation
            processor_generation = generation
            self._emit_result(self.manager.repetitions(), "READY", "Ready", generation)
            while not self.isInterruptionRequested():
                frame_started_at = monotonic()
                frame = camera.read()
                if frame is None:
                    if not self.isInterruptionRequested():
                        self.error.emit("Camera frame unavailable. Check the camera connection.")
                    break
                # Mirror before inference so the preview and pose skeleton use
                # the same left/right orientation.
                frame = cv2.flip(frame, 1)
                detected = pose_detector.detect(frame)
                fps = self._update_fps()
                if not detected:
                    self._draw(frame, {}, {}, person_detected=False, fps=fps, posture_status="tracking lost")
                    self._emit_frame(frame)
                    generation = self.manager.generation
                    self._emit_result(self.manager.repetitions(), "NO PERSON", "No person detected", generation)
                    self._emit_debug({}, "", generation, frame_started_at)
                    self._emit_telemetry(0.0, fps, generation, frame_started_at)
                    self._sleep_to_target(frame_started_at)
                    continue
                current_generation = self.manager.generation
                if current_generation != processor_generation:
                    # Landmark moving averages belong to the exercise
                    # generation in which they were collected.
                    processor.reset()
                    processor_generation = current_generation
                landmarks = processor.process(detected)
                generation, result = self.manager.process_snapshot(landmarks)
                angles = result.angles
                tracking = 100.0 * sum(point.visibility for point in landmarks.values()) / len(landmarks)
                self._draw(frame, landmarks, angles, person_detected=True, fps=fps, posture_status=result.status)
                self._emit_frame(frame)
                self._emit_result(result.repetitions, result.state, result.status, generation)
                self._emit_debug(angles, result.debug, generation, frame_started_at)
                self._emit_telemetry(tracking, fps, generation, frame_started_at)
                self._sleep_to_target(frame_started_at)
        except Exception as exc:
            log.exception("Camera worker failed")
            if phase == "camera":
                message = "Camera unavailable. Check the connection and camera permission."
            elif phase == "model":
                message = "Pose model failed to load. Restart the app or reinstall the dependencies."
            else:
                message = "Camera processing stopped unexpectedly. Press Start Camera to retry."
            self.error.emit(f"{message}\n\nDetails: {exc}")
        finally:
            try:
                camera.release()
            except Exception:
                log.exception("Camera release failed")
            try:
                pose_detector.close()
            except Exception:
                log.exception("Pose detector shutdown failed")
            log.info("Camera worker stopped and resources were released")

    @staticmethod
    def _to_qimage(frame) -> QImage:
        cv2 = CameraWorker._opencv()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return QImage(
            rgb.data,
            rgb.shape[1],
            rgb.shape[0],
            rgb.strides[0],
            QImage.Format.Format_RGB888,
        ).copy()

    @staticmethod
    def _sleep_to_target(frame_started_at: float) -> None:
        remaining = (1 / SETTINGS.target_fps) - (monotonic() - frame_started_at)
        if remaining > 0:
            sleep(remaining)

    def _emit_result(self, repetitions: int, state: str, status: str, generation: int) -> None:
        payload = (repetitions, state, status, generation)
        if payload != self._last_result:
            self._last_result = payload
            self.result_ready.emit(*payload)

    def _emit_frame(self, frame) -> None:
        if self._frame_pending.is_set():
            return
        self._frame_pending.set()
        self.frame_ready.emit(self._to_qimage(frame))

    def frame_consumed(self) -> None:
        self._frame_pending.clear()

    def _emit_debug(self, angles: dict, debug: str, generation: int, timestamp: float) -> None:
        if timestamp - self._last_debug_at < 0.2:
            return
        self._last_debug_at = timestamp
        self.angles_ready.emit(angles, generation)
        self.exercise_debug_ready.emit(debug, generation)

    def _emit_telemetry(self, tracking: float, fps: float, generation: int, timestamp: float) -> None:
        if timestamp - self._last_telemetry_at < 0.1:
            return
        self._last_telemetry_at = timestamp
        self.telemetry_ready.emit(tracking, fps, generation)

    def _update_fps(self) -> float:
        now = monotonic()
        if self._last_frame_at is not None:
            instantaneous = 1 / max(now - self._last_frame_at, 0.001)
            self._fps = instantaneous if self._fps == 0 else (0.2 * instantaneous + 0.8 * self._fps)
        self._last_frame_at = now
        return self._fps

    def _draw(self, frame, landmarks, angles, person_detected: bool = True,
              fps: float = 0.0, posture_status: str = "") -> None:
        cv2 = self._opencv()
        height, width = frame.shape[:2]
        skeleton_color = self._skeleton_color(posture_status, person_detected)
        for a, b in self._CONNECTIONS:
            if a in landmarks and b in landmarks and landmarks[a].visibility > 0.4 and landmarks[b].visibility > 0.4:
                cv2.line(frame, (int(landmarks[a].x * width), int(landmarks[a].y * height)), (int(landmarks[b].x * width), int(landmarks[b].y * height)), skeleton_color, 3)
        for point in landmarks.values():
            if point.visibility > 0.4:
                cv2.circle(frame, (int(point.x * width), int(point.y * height)), 4, skeleton_color, -1)
        confidence = sum(point.visibility for point in landmarks.values()) / len(landmarks) if landmarks else 0.0
        lines = [
            f"Person: {'detected' if person_detected else 'not detected'}",
            f"FPS: {fps:.1f}",
            f"Confidence: {confidence:.0%}",
        ]
        for index, text in enumerate(lines):
            cv2.putText(frame, text, (16, 30 + index * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)
        for name, value in angles.items():
            if name not in JOINT_ANGLE_TRIPLES:
                continue
            _, joint, _ = JOINT_ANGLE_TRIPLES[name]
            point = landmarks[joint]
            cv2.putText(frame, f"{value:.0f}°", (int(point.x * width) + 6, int(point.y * height) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (253, 224, 71), 2)

    @staticmethod
    def _skeleton_color(status: str, person_detected: bool) -> tuple[int, int, int]:
        if not person_detected:
            return 148, 148, 148
        normalized = status.lower()
        if any(word in normalized for word in ("bad", "lost", "not visible", "standing", "rejected")):
            return 68, 68, 239
        if any(word in normalized for word in ("partial", "between thresholds", "move ")):
            return 11, 158, 245
        return 94, 197, 34

    @classmethod
    def _opencv(cls):
        if cls._cv2 is None:
            import cv2

            cls._cv2 = cv2
        return cls._cv2

    def stop(self) -> None:
        self.requestInterruption()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.manager = ExerciseManager()
        self.storage, self.session_storage, self.started_at = WorkoutStorage(), SessionManager(), None
        self.worker: CameraWorker | None = None
        self.timer = TimerController()
        self.metrics = LiveWorkoutMetrics()
        self.timer_enabled = True
        self._last_reps = 0
        self._exercise_generation = self.manager.generation
        self._session_finished = False
        self._session_saved = False
        self._camera_stopping = False
        self._close_requested = False
        self._restart_after_stop = False
        self._tracking = 0.0
        self._fps = 0.0
        self._form_score = 0.0
        self._last_state = "READY"
        self._last_status = "Ready"
        self._timer_text = "00:00"
        self._countdown_active = False
        self._countdown_started = False
        self._countdown_index = 0
        self._summary_dialog: WorkoutSummaryDialog | None = None
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(800)
        self._countdown_timer.timeout.connect(self._advance_countdown)
        self.timer.changed.connect(self._timer_changed)
        self.timer.finished.connect(self._timer_finished)
        self._retired_workers: list[CameraWorker] = []
        self.setWindowTitle("Bộ đếm bài tập")
        self.setMinimumSize(1100, 700)
        self.resize(1440, 900)
        self.setStyleSheet(load_theme())
        self._build()
        self._install_shortcuts()

    def _build(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        self.header = Header()
        layout.addWidget(self.header)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        layout.addWidget(self.tabs, 1)

        workout_page = QWidget()
        workout_layout = QVBoxLayout(workout_page)
        workout_layout.setContentsMargins(0, 10, 0, 0)
        workout_layout.setSpacing(10)
        body = QHBoxLayout()
        body.setSpacing(12)

        self.sidebar = Sidebar(self.manager.names)
        self.sidebar.setMinimumWidth(230)
        self.sidebar.setMaximumWidth(280)
        self.selector = self.sidebar.selector
        self.selector.currentIndexChanged.connect(self._change_exercise)
        self.start_button = self.sidebar.start
        self.stop_button = self.sidebar.stop
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop_camera)
        self.sidebar.reset.clicked.connect(self.reset)
        self.sidebar.pause.clicked.connect(self._toggle_pause)
        self.sidebar.timer_enabled.toggled.connect(self._set_timer_enabled)
        self.sidebar.apply_timer.clicked.connect(self._apply_timer_settings)
        self.sidebar.debug_mode.toggled.connect(self._toggle_debug)
        self.sidebar.goals_changed.connect(self._goals_changed)
        self.sidebar.settings.clicked.connect(lambda: self.tabs.setCurrentIndex(3))
        body.addWidget(self.sidebar)

        center = QVBoxLayout()
        center.setSpacing(10)
        self.camera_view = CameraWidget()
        center.addWidget(self.camera_view, 1)

        status_bar = QFrame()
        status_bar.setObjectName("compactStatus")
        status_layout = QHBoxLayout(status_bar)
        self.count_caption = QLabel("Chống đẩy:")
        self.reps = value_label("0", 30)
        self.person = value_label("Người: chưa phát hiện", 14)
        self.state = value_label("Trạng thái: Sẵn sàng", 15)
        status_layout.addWidget(self.count_caption)
        status_layout.addWidget(self.reps)
        status_layout.addSpacing(16)
        status_layout.addWidget(self.state, 1)
        status_layout.addWidget(self.person)
        center.addWidget(status_bar)

        self.workout_status = WorkoutStatusPanel()
        center.addWidget(self.workout_status)
        body.addLayout(center, 1)

        self.debug_drawer = DebugPanel()
        self.debug_drawer.setMinimumWidth(230)
        self.debug_drawer.setMaximumWidth(300)
        self.debug_drawer.setVisible(False)
        body.addWidget(self.debug_drawer)
        workout_layout.addLayout(body, 1)

        self.stats = StatsPanel()
        workout_layout.addWidget(self.stats)
        self.tabs.addTab(workout_page, "Tập luyện")
        self.tabs.addTab(self._placeholder("LỊCH SỬ", "Lịch sử buổi tập sẽ xuất hiện tại đây."), "Lịch sử")
        self.posture_guide = PostureGuide()
        self.tabs.addTab(self.posture_guide, "Hướng dẫn")
        self.tabs.addTab(self._placeholder("CÀI ĐẶT", "Các tùy chọn bài tập và hẹn giờ nằm trong bảng điều khiển."), "Cài đặt")

        self.timer_card = TimerWidget()
        self.timer_card.setParent(root)
        self.timer_card.hide()
        self.angle_debug = self.debug_drawer.angle_content
        self.exercise_debug = self.debug_drawer.exercise_content
        self.workout_status.update_goal(0, self.sidebar.target_reps.value(), self.sidebar.target_sets.value())
        self._update_camera_hud()
        self._update_dashboard()
        self.setCentralWidget(root)

    @staticmethod
    def _placeholder(title: str, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch()
        heading = QLabel(title)
        heading.setObjectName("placeholderTitle")
        description_label = QLabel(description)
        description_label.setObjectName("muted")
        layout.addWidget(heading, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return page

    @Slot()
    def start(self) -> None:
        if self.worker is not None:
            return
        if self.started_at is None or self.manager.repetitions() == 0:
            self.started_at = datetime.now()
        self._session_finished = False
        self._session_saved = False
        self._camera_stopping = False
        self._countdown_started = False
        self._cancel_countdown()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.camera_view.show_starting()
        self.state.setText("Trạng thái: Đang khởi động camera...")
        self.person.setText("Người: đang chờ")
        self.header.set_status("Đang mở camera", "Mô hình đang chờ")
        self.worker = CameraWorker(self.manager)
        self._retired_workers.append(self.worker)
        self.worker.frame_ready.connect(self._update_frame); self.worker.result_ready.connect(self.update_result)
        self.worker.angles_ready.connect(self.update_angles)
        self.worker.exercise_debug_ready.connect(self.update_exercise_debug)
        self.worker.telemetry_ready.connect(self.update_telemetry)
        self.worker.error.connect(self.show_error); self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    @Slot(QImage)
    def _update_frame(self, image: QImage) -> None:
        worker = self.sender()
        self.camera_view.set_frame(image)
        if isinstance(worker, CameraWorker):
            worker.frame_consumed()

    @Slot()
    def stop_camera(self) -> None:
        worker = self.worker
        if worker is None:
            return
        self.state.setText("Trạng thái: Camera đã tắt")
        self._camera_stopping = True
        self._cancel_countdown()
        self.person.setText("Người: chưa phát hiện")
        self.camera_view.show_stopped()
        self.header.set_status("Camera đã dừng", "Đang giải phóng mô hình")
        self.header.set_fps(0.0)
        self._fps = 0.0
        self._tracking = 0.0
        self.stop_button.setEnabled(False)
        self.timer.pause()
        self.sidebar.pause.setEnabled(False)
        worker.stop()

    @Slot(int, str, str, int)
    def update_result(self, repetitions: int, state: str, status: str, generation: int) -> None:
        if generation != self._exercise_generation or self._session_finished or self._camera_stopping:
            return
        self._last_state, self._last_status = state, status
        self.reps.setText(str(repetitions))
        self.state.setText(f"Trạng thái: {translate_state(state)} — {translate_status(status)}")
        if state == "INITIALIZING":
            self.person.setText("Người: đang chờ")
            if status == "Opening camera":
                self.header.set_status("Đang mở camera", "Mô hình đang chờ")
            else:
                self.header.set_status("Camera đã mở", "Đang tải mô hình")
        elif state == "READY":
            self.person.setText("Người: đang chờ")
            self.header.set_status("Camera đã mở", "Mô hình sẵn sàng")
            if not self._countdown_started:
                self._begin_countdown()
        else:
            self.person.setText("Người: chưa phát hiện" if state == "NO PERSON" else "Người: đã phát hiện")

        added = max(0, repetitions - self._last_reps)
        if added and not self._countdown_active:
            if self.timer_enabled:
                self.timer.start_on_rep()
            self.metrics.record_repetitions(added, monotonic())
        if status and state not in {"INITIALIZING", "READY", "NO PERSON"}:
            self._update_coach(status, state, added > 0)
        self._last_reps = repetitions
        self.workout_status.update_goal(
            self.metrics.repetitions,
            self.sidebar.target_reps.value(),
            self.sidebar.target_sets.value(),
        )
        self._update_camera_hud()
        self._update_dashboard()

    def _timer_changed(self, state: str, value: str) -> None:
        self.timer_card.value.setText(value if state != "READY" else "SẴN SÀNG")
        self._timer_text = value if state != "READY" else "READY"
        self.header.set_timer(value if self.timer_enabled else "TẮT")
        self.sidebar.pause.setText("Tiếp tục" if state == "PAUSED" else "Tạm dừng")
        self.sidebar.pause.setEnabled(self.timer_enabled and self.worker is not None and state in {"RUNNING", "PAUSED"})
        self._update_camera_hud()
        self._update_dashboard()

    @Slot(float, float, int)
    def update_telemetry(self, tracking: float, fps: float, generation: int) -> None:
        if generation != self._exercise_generation or self._camera_stopping:
            return
        self._tracking, self._fps = tracking, fps
        self.header.set_fps(fps)
        score, grade, color, valid = self._quality_for_status(tracking, self._last_status, self._last_state)
        self._form_score = score
        if tracking > 0 and self._last_state not in {"INITIALIZING", "READY", "NO PERSON"}:
            self.metrics.update_quality(score, valid)
        self.workout_status.update_quality(score, tracking, grade, color)
        self._update_camera_hud()
        self._update_dashboard()

    @staticmethod
    def _quality_for_status(tracking: float, status: str, state: str) -> tuple[float, str, str, bool]:
        normalized = status.lower()
        # Exercise detectors may provide a weighted, temporally smoothed score.
        # Keep the presentation generic while using that richer result.
        marker = "form score:"
        if marker in normalized:
            try:
                score = float(normalized.split(marker, 1)[1].split("%", 1)[0].strip())
            except ValueError:
                pass
            else:
                score = max(0.0, min(100.0, score))
                valid = "posture: bad" not in normalized
                if not valid or score < 60:
                    return score, "Cần điều chỉnh", "#EF4444", False
                if score < 75:
                    return score, "Chấp nhận được", "#F59E0B", True
                if score < 90:
                    return score, "Tốt", "#3B82F6", True
                return score, "Xuất sắc", "#22C55E", True
        if tracking < 40 or state == "NO PERSON":
            return tracking * 0.5, "Mất theo dõi", "#94a3b8", False
        if any(word in normalized for word in ("bad", "lost", "not visible", "standing", "rejected")):
            return min(64.0, tracking * 0.65), "Cần điều chỉnh", "#EF4444", False
        if any(word in normalized for word in ("partial", "between thresholds", "move ")):
            return min(84.0, tracking * 0.86), "Chấp nhận được", "#F59E0B", True
        return min(99.0, 85.0 + tracking * 0.14), "Xuất sắc", "#22C55E", True

    def _update_coach(self, status: str, state: str, completed_rep: bool) -> None:
        normalized = status.lower()
        if str(self.selector.currentData()) == "crunch":
            self._update_crunch_coach(normalized, state, completed_rep)
            return
        if completed_rep:
            self.workout_status.set_coach("Nhịp độ tốt — tiếp tục phát huy!", "#22C55E")
        elif "hips too" in normalized:
            self.workout_status.set_coach("Giữ hông thẳng hàng với vai và đầu gối.", "#F59E0B")
        elif "partial" in normalized or "between thresholds" in normalized:
            self.workout_status.set_coach("Hạ thấp thêm một chút để hoàn thành biên độ.", "#F59E0B")
        elif "standing" in normalized:
            self.workout_status.set_coach("Vào đúng tư thế bắt đầu và giữ cơ thể trong khung hình.", "#EF4444")
        elif "not visible" in normalized or "move " in normalized:
            self.workout_status.set_coach("Điều chỉnh vị trí để camera nhìn rõ toàn bộ cơ thể.", "#F59E0B")
        elif state in {"UP", "DOWN"}:
            self.workout_status.set_coach("Tư thế tốt — giữ chuyển động ổn định.", "#22C55E")

    def _update_crunch_coach(self, status: str, state: str, completed_rep: bool) -> None:
        if completed_rep:
            self.workout_status.set_coach("Một lần gập bụng tốt — tiếp tục!", "#22C55E")
        elif "neck" in status:
            self.workout_status.set_coach("Giữ cổ tự nhiên, không dùng tay kéo đầu.", "#F59E0B")
        elif "lower back" in status:
            self.workout_status.set_coach("Giữ lưng dưới ổn định trên sàn.", "#F59E0B")
        elif "slowly" in status or "control" in status:
            self.workout_status.set_coach("Di chuyển chậm và có kiểm soát.", "#F59E0B")
        elif "lift your shoulders" in status or "full range" in status:
            self.workout_status.set_coach("Nâng vai cao hơn để đủ biên độ.", "#F59E0B")
        elif "lie back" in status:
            self.workout_status.set_coach("Nằm xuống hoàn toàn để vào tư thế bắt đầu.", "#F59E0B")
        elif any(word in status for word in ("standing", "sitting", "sideways", "inside the frame")):
            self.workout_status.set_coach("Nằm nghiêng với toàn bộ cơ thể trong khung hình.", "#EF4444")
        elif state == "UP":
            self.workout_status.set_coach("Hạ vai xuống từ từ và giữ lưng dưới ổn định.", "#22C55E")
        elif state == "DOWN":
            self.workout_status.set_coach("Sẵn sàng — nâng vai bằng cơ bụng.", "#22C55E")

    def _update_camera_hud(self) -> None:
        self.camera_view.set_hud(
            translate_exercise(self.manager.selected.name),
            translate_state(self._last_state),
            self.metrics.repetitions,
            self._timer_text if self.timer_enabled else "TẮT",
            self._fps,
            self._tracking,
            self._form_score,
        )

    def _update_dashboard(self) -> None:
        snapshot = self.metrics.snapshot(self.timer.elapsed_seconds)
        self.stats.update_values({
            "Số lần hôm nay": str(snapshot.repetitions),
            "Thời gian tập": f"{int(snapshot.duration)//60:02}:{int(snapshot.duration)%60:02}",
            "Tốc độ hiện tại": speed_label(snapshot.current_rep_seconds),
            "Tốc độ trung bình": speed_label(snapshot.average_rep_seconds),
            "Độ chính xác": f"{snapshot.accuracy:.0f}%" if snapshot.repetitions else "—",
            "Chất lượng tư thế": f"{snapshot.form_score:.0f}%" if self._tracking else "—",
            "FPS": f"{self._fps:.0f}",
        })

    def _set_timer_enabled(self, enabled: bool) -> None:
        self.timer_enabled = enabled
        for widget in (self.sidebar.timer_mode, self.sidebar.timer_duration,
                       self.sidebar.custom_duration, self.sidebar.apply_timer):
            widget.setEnabled(enabled)
        if not enabled:
            self.timer.reset()
            self.header.set_timer("TẮT")
        self._update_camera_hud()

    def _apply_timer_settings(self) -> None:
        try:
            self.timer.configure(str(self.sidebar.timer_mode.currentData()), self.sidebar.selected_duration())
        except (TypeError, ValueError) as exc:
            log.warning("Invalid timer settings: %s", exc)
            QMessageBox.warning(self, "Cài đặt hẹn giờ", "Không thể áp dụng thời gian đã chọn.")

    def _timer_finished(self, duration: float) -> None:
        self._session_finished = True
        QApplication.beep()
        snapshot = self.metrics.snapshot(duration)
        self.stop_camera()
        self._summary_dialog = WorkoutSummaryDialog(
            translate_exercise(self.manager.selected.name), snapshot, self
        )
        self._summary_dialog.new_session_requested.connect(self._start_new_session)
        self._summary_dialog.save_requested.connect(lambda: self._save_session(snapshot))
        self._summary_dialog.show()

    def _save_session(self, snapshot) -> None:
        if self._session_saved:
            return
        try:
            self.session_storage.save({
                "exercise": str(self.selector.currentData()),
                "start": self.started_at.isoformat() if self.started_at else datetime.now().isoformat(),
                "duration": round(snapshot.duration, 1),
                "reps": snapshot.repetitions,
                "rpm": round(snapshot.reps_per_minute, 1),
                "accuracy": round(snapshot.accuracy, 1),
                "best_streak": snapshot.best_streak,
            })
        except (OSError, ValueError) as exc:
            log.exception("Could not save workout session")
            QMessageBox.warning(self, "Không thể lưu buổi tập", str(exc))
            return
        self._session_saved = True
        if self._summary_dialog:
            self._summary_dialog.mark_saved()

    def _start_new_session(self) -> None:
        if self._summary_dialog:
            self._summary_dialog.close()
        self.reset()
        if self.worker is None:
            self.start()
        else:
            self._restart_after_stop = True

    @Slot(dict, int)
    def update_angles(self, angles: dict, generation: int) -> None:
        if generation != self._exercise_generation or self._camera_stopping:
            return
        if not angles:
            self.angle_debug.setText("Joint angles: no pose detected")
            return
        values = "   ".join(f"{name}: {value:.0f}°" for name, value in angles.items())
        self.angle_debug.setText(f"Joint angles\n{values}")

    @Slot(str, int)
    def update_exercise_debug(self, debug: str, generation: int) -> None:
        if generation != self._exercise_generation or self._camera_stopping:
            return
        self.exercise_debug.setText(debug if debug else "Exercise debug: no pose detected")

    @Slot()
    def reset(self) -> None:
        self.manager.reset()
        self._exercise_generation = self.manager.generation
        self.metrics.reset()
        self.started_at = datetime.now()
        self._reset_session_ui()

    def _reset_session_ui(self) -> None:
        self.reps.setText("0")
        self.state.setText("Trạng thái: Sẵn sàng")
        self._last_reps = 0
        self._last_state = "READY"
        self._last_status = "Ready"
        self._form_score = 0.0
        self._session_finished = False
        self._session_saved = False
        self.sidebar.pause.setText("Tạm dừng")
        self.timer.reset()
        self.workout_status.update_goal(0, self.sidebar.target_reps.value(), self.sidebar.target_sets.value())
        self.workout_status.set_coach("Sẵn sàng cho lần lặp đầu tiên.")
        self._update_camera_hud()
        self._update_dashboard()

    @Slot(int)
    def _change_exercise(self, _index: int) -> None:
        key = str(self.selector.currentData())
        try:
            self.manager.select(key)
        except (KeyError, RuntimeError) as exc:
            log.exception("Exercise switch failed")
            self.show_error(f"Exercise module failed: {exc}")
            return
        self._exercise_generation = self.manager.generation
        self.metrics.reset()
        self._reset_session_ui()
        self.count_caption.setText("Chống đẩy:" if key == "push_up" else f"{translate_exercise(self.manager.selected.name)}:")
        self.header.set_exercise(translate_exercise(self.manager.selected.name))
        self.posture_guide.set_exercise(key)
        self._countdown_started = False
        if self.worker is not None and not self._camera_stopping:
            self._begin_countdown()

    @Slot(bool)
    def _toggle_debug(self, enabled: bool) -> None:
        self.debug_drawer.setVisible(enabled)

    @Slot(int, int)
    def _goals_changed(self, target_reps: int, target_sets: int) -> None:
        self.workout_status.update_goal(self.metrics.repetitions, target_reps, target_sets)

    def _begin_countdown(self) -> None:
        if self._countdown_started or self._camera_stopping or self.worker is None:
            return
        self._countdown_started = True
        self._countdown_active = True
        self._countdown_index = 0
        self.camera_view.show_countdown("3")
        self._countdown_timer.start()

    @Slot()
    def _advance_countdown(self) -> None:
        steps = ("3", "2", "1", "GO!")
        self._countdown_index += 1
        if self._countdown_index < len(steps):
            self.camera_view.show_countdown(steps[self._countdown_index])
            return
        self._countdown_timer.stop()
        self.camera_view.show_countdown(None)
        self._countdown_active = False
        self.manager.reset()
        self._exercise_generation = self.manager.generation
        self.metrics.reset()
        self._last_reps = 0
        self.reps.setText("0")
        self.started_at = datetime.now()
        self.timer.reset()
        self.workout_status.update_goal(0, self.sidebar.target_reps.value(), self.sidebar.target_sets.value())
        self.workout_status.set_coach("Bắt đầu — giữ nhịp ổn định!", "#22C55E")
        self._update_camera_hud()

    def _cancel_countdown(self) -> None:
        self._countdown_timer.stop()
        self._countdown_active = False
        if hasattr(self, "camera_view"):
            self.camera_view.show_countdown(None)

    def _install_shortcuts(self) -> None:
        self._shortcuts = []
        for sequence, callback in (
            ("Space", self._toggle_camera),
            ("R", self.reset),
            ("P", self._toggle_pause),
            ("Escape", self.close),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    @Slot()
    def _toggle_camera(self) -> None:
        if self.worker is None:
            self.start()
        elif not self._camera_stopping:
            self.stop_camera()

    @Slot()
    def _toggle_pause(self) -> None:
        if self.timer.state is TimerState.RUNNING:
            self.timer.pause()
            self.sidebar.pause.setText("Tiếp tục")
        elif self.timer.state is TimerState.PAUSED:
            self.timer.resume()
            self.sidebar.pause.setText("Tạm dừng")

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
        if not any(item is worker for item in self._retired_workers):
            return
        worker.wait()
        self._retired_workers.remove(worker)
        if self.worker is worker:
            self.worker = None
            self._camera_stopping = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.state.setText("Trạng thái: Camera đã tắt")
            self.person.setText("Người: chưa phát hiện")
            self.camera_view.show_stopped()
            self.header.set_status("Camera đã dừng", "Mô hình chưa tải")
            self.header.set_fps(0.0)
            self.workout_status.update_quality(0.0, 0.0, "Đang chờ", "#94a3b8")
        worker.deleteLater()
        if self._close_requested:
            QTimer.singleShot(0, self.close)
        elif self._restart_after_stop:
            self._restart_after_stop = False
            QTimer.singleShot(0, self.start)

    def closeEvent(self, event) -> None:
        if self.worker:
            self._close_requested = True
            self.stop_camera()
            event.ignore()
            return
        repetitions = self.metrics.repetitions or self.manager.repetitions()
        if self.started_at and repetitions:
            try:
                self.storage.append(Workout.create(self.manager.selected.name, repetitions, self.started_at, datetime.now()))
            except (OSError, ValueError) as exc:
                log.exception("Could not save workout history")
                QMessageBox.warning(self, "Không thể lưu buổi tập", f"Dữ liệu buổi tập chưa được lưu.\n\nChi tiết: {exc}")
        event.accept()
