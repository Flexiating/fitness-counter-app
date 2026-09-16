from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel
from app.ui.translations import tr


class CameraWidget(QLabel):
    """Video surface with lightweight child-label overlays."""

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(640, 360)
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

        self.show_stopped()

    def show_stopped(self) -> None:
        self._fade.stop()
        self._opacity.setOpacity(1.0)
        self._last_image = None
        self._first_frame_pending = False
        self._accept_frames = False
        self.clear()
        self.setText(f"📷\n\n{tr('camera.stopped')}\n{tr('camera.press_start')}")
        self._set_hud_visible(False)
        self.countdown.hide()

    def show_starting(self) -> None:
        self._fade.stop()
        self._opacity.setOpacity(1.0)
        self._last_image = None
        self._first_frame_pending = True
        self._accept_frames = True
        self.clear()
        self.setText(f"📷\n\n{tr('camera.starting')}")
        self._set_hud_visible(False)
        self.countdown.hide()

    @Slot(QImage)
    def set_frame(self, image: QImage) -> None:
        if not self._accept_frames:
            return
        self._last_image = image
        self.setText("")
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
        self.hud_info.setText(f"{exercise}\n{state}\n{tr('metric.reps', value=repetitions)}")
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

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        width = self.width()
        margin = max(14, width // 70)
        self.hud_info.setGeometry(QRect(margin, margin, 168, 82))
        self.hud_metrics.setGeometry(QRect(max(margin, width - 178 - margin), margin, 178, 82))
        self.hud_timer.setGeometry(QRect(max(0, width // 2 - 74), max(margin, self.height() - 48 - margin), 148, 38))
        self.countdown.setGeometry(self.rect())
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
