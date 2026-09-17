from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from app.ui.translations import tr


class Header(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("headerCard")
        self._camera_status_key = "camera.stopped"
        self._model_status_key = "camera.model_unloaded"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 14, 22, 14)

        title_column = QVBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("appTitle")
        self.exercise = QLabel()
        self.exercise.setObjectName("exerciseTitle")
        title_column.addWidget(self.title)
        title_column.addWidget(self.exercise)
        layout.addLayout(title_column)
        layout.addStretch()

        self.metric_headings: list[QLabel] = []
        self.camera = self._metric(layout, "", "")
        self.model = self._metric(layout, "", "")
        self.fps = self._metric(layout, "", "— FPS")
        self.workout_timer = self._metric(layout, "", "00:00")
        self.clock = self._metric(layout, "", "--:--")
        # Technical telemetry remains available in the camera HUD / debug drawer.
        for label in (self.model, self.fps, self.metric_headings[1], self.metric_headings[2]):
            label.hide()
        self.meta = QLabel()
        self.meta.hide()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1_000)
        self.retranslate()
        self.refresh()

    def _metric(self, parent: QHBoxLayout, title: str, value: str) -> QLabel:
        column = QVBoxLayout()
        heading = QLabel(title)
        heading.setObjectName("sectionLabel")
        self.metric_headings.append(heading)
        label = QLabel(value)
        label.setObjectName("headerValue")
        column.addWidget(heading)
        column.addWidget(label)
        parent.addSpacing(22)
        parent.addLayout(column)
        return label

    def set_status(self, camera: str, model: str) -> None:
        self._camera_status_key = camera
        self._model_status_key = model
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
        camera_status = tr(self._camera_status_key)
        model_status = tr(self._model_status_key)
        self.camera.setText(camera_status)
        self.model.setText(model_status)
        self.clock.setText(f"{datetime.now():%H:%M}")
        self.meta.setText(f"{camera_status} • {model_status} • {datetime.now():%H:%M}")

    def retranslate(self) -> None:
        self.title.setText(tr("app.title"))
        headings = ("camera.label", "model.label", "performance.label", "time.label", "now.label")
        for label, key in zip(self.metric_headings, headings):
            label.setText(tr(key))
        self.refresh()
