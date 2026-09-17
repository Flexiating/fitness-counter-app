from __future__ import annotations
from html import escape

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, Slot, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel
from app.ui.translations import tr
from app.ui.design import Button, CameraGlyph, ProgressRing


class CameraWidget(QLabel):
    """Video surface with lightweight child-label overlays."""
    start_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(420, 300)
        self.setObjectName("cameraSurface")
        self._last_image: QImage | None = None
        self._first_frame_pending = False
        self._accept_frames = False
        self._last_hud: tuple[object, ...] | None = None
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(200)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.hud_info = QLabel(self)
        self.hud_info.setObjectName("cameraHud")
        self.hud_info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.hud_metrics = QLabel(self)
        self.hud_metrics.setObjectName("cameraHud")
        self.hud_metrics.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.hud_timer = QLabel(self)
        self.hud_timer.setObjectName("cameraTimer")
        self.hud_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown = QLabel(self)
        self.countdown.setObjectName("cameraCountdown")
        self.countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown.hide()

        self.start_action = Button(self, shadow=False)
        self.start_action.setObjectName("primaryButton")
        self.start_action.clicked.connect(self.start_requested)
        self.camera_icon = CameraGlyph(self)
        self.progress_ring = ProgressRing(self)

        self.show_stopped()

    def show_stopped(self) -> None:
        self._fade.stop()
        self._opacity.setOpacity(1.0)
        self._last_image = None
        self._first_frame_pending = False
        self._accept_frames = False
        self.clear()
        self.setText(f"{tr('ui.camera_off')}\n{tr('camera.press_start')}")
        self.setAccessibleName(tr('ui.camera_off'))
        self.camera_icon.show()
        self.camera_icon.set_loading(False)
        self._set_hud_visible(False)
        self.countdown.hide()
        self.start_action.setText(tr("button.start_camera"))
        self.start_action.show()

    def show_starting(self) -> None:
        self._fade.stop()
        self._opacity.setOpacity(1.0)
        self._last_image = None
        self._first_frame_pending = True
        self._accept_frames = True
        self.clear()
        self.setText(tr('camera.starting'))
        self.camera_icon.show()
        self.camera_icon.set_loading(True)
        self._set_hud_visible(False)
        self.countdown.hide()
        self.start_action.hide()

    @Slot(QImage)
    def set_frame(self, image: QImage) -> None:
        if not self._accept_frames:
            return
        self._last_image = image
        self.setText("")
        self.camera_icon.hide()
        self.camera_icon.set_loading(False)
        self._render_image()
        self._set_hud_visible(True)
        if self._first_frame_pending:
            self._first_frame_pending = False
            self._fade.stop()
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.start()

    def set_hud(self, exercise: str, state: str, repetitions: int, timer: str,
                fps: float, tracking: float, form_score: float) -> None:
        payload = (exercise, state, repetitions, timer, round(fps), round(tracking), round(form_score))
        if payload == self._last_hud:
            return
        self._last_hud = payload
        self.hud_info.setText(f"{escape(exercise)}<br><span style='color:#A9B4C4'>{escape(state)}</span><br><span style='font-size:28px;font-weight:700'>{tr('metric.reps', value=repetitions)}</span>")
        self.hud_metrics.setText(
            f"{round(fps)} FPS\n{tr('metric.tracking', value=round(tracking))}\n{tr('metric.form', value=round(form_score))}"
        )
        self.hud_timer.setText(f"⏱  {timer}")

    def retranslate(self) -> None:
        if not self._accept_frames:
            self.show_stopped()
        self._last_hud = None

    def show_countdown(self, value: str | None) -> None:
        if value is None:
            self.countdown.hide()
            return
        self.countdown.setText(value)
        self.countdown.show()
        self.countdown.raise_()

    def _set_hud_visible(self, visible: bool) -> None:
        self.hud_info.setVisible(visible)
        self.hud_metrics.setVisible(visible)
        self.hud_timer.setVisible(visible)
        self.progress_ring.setVisible(visible)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        width = self.width()
        margin = max(14, width // 70)
        self.hud_info.setGeometry(QRect(margin, margin, 190, 112))
        self.hud_metrics.setGeometry(QRect(max(margin, width - 178 - margin), margin, 178, 82))
        self.hud_timer.setGeometry(QRect(max(0, width // 2 - 74), max(margin, self.height() - 48 - margin), 148, 38))
        self.countdown.setGeometry(self.rect())
        self.start_action.setGeometry(max(12, width // 2 - 100), self.height() // 2 + 80, 200, 48)
        self.camera_icon.move(width // 2 - 32, self.height() // 2 - 100)
        self.progress_ring.move(max(8, width // 2 - 148), max(8, self.height() - 88))
        if self._last_image is not None:
            self._render_image()

    def _render_image(self) -> None:
        if self._last_image is None:
            return
        self.setPixmap(
            QPixmap.fromImage(self._last_image).scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        )
