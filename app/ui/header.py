from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class Header(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("headerCard")
        self._camera_status = "Camera đã dừng"
        self._model_status = "Mô hình chưa tải"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 14, 22, 14)

        title_column = QVBoxLayout()
        self.title = QLabel("WORKOUT TRACKER")
        self.title.setObjectName("appTitle")
        self.exercise = QLabel("Chống đẩy")
        self.exercise.setObjectName("exerciseTitle")
        title_column.addWidget(self.title)
        title_column.addWidget(self.exercise)
        layout.addLayout(title_column)
        layout.addStretch()

        self.camera = self._metric(layout, "CAMERA", self._camera_status)
        self.model = self._metric(layout, "MÔ HÌNH", self._model_status)
        self.fps = self._metric(layout, "HIỆU NĂNG", "— FPS")
        self.workout_timer = self._metric(layout, "THỜI GIAN", "00:00")
        self.clock = self._metric(layout, "BÂY GIỜ", "--:--")
        self.meta = QLabel()
        self.meta.hide()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1_000)
        self.refresh()

    @staticmethod
    def _metric(parent: QHBoxLayout, title: str, value: str) -> QLabel:
        column = QVBoxLayout()
        heading = QLabel(title)
        heading.setObjectName("sectionLabel")
        label = QLabel(value)
        label.setObjectName("headerValue")
        column.addWidget(heading)
        column.addWidget(label)
        parent.addSpacing(22)
        parent.addLayout(column)
        return label

    def set_status(self, camera: str, model: str) -> None:
        self._camera_status = camera
        self._model_status = model
        self.refresh()

    def set_exercise(self, exercise: str) -> None:
        self.exercise.setText(exercise)

    def set_fps(self, fps: float) -> None:
        value = f"{fps:.0f} FPS" if fps > 0 else "— FPS"
        if self.fps.text() != value:
            self.fps.setText(value)

    def set_timer(self, value: str) -> None:
        if self.workout_timer.text() != value:
            self.workout_timer.setText(value)

    def refresh(self) -> None:
        self.camera.setText(self._camera_status)
        self.model.setText(self._model_status)
        self.clock.setText(f"{datetime.now():%H:%M}")
        self.meta.setText(f"{self._camera_status} • {self._model_status} • {datetime.now():%H:%M}")
