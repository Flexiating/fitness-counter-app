from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from app.ui.translations import tr


class StatsPanel(QFrame):
    KEYS = (
        "metric.reps_today", "metric.workout_time", "metric.current_speed",
        "metric.average_speed", "metric.accuracy", "metric.posture", "metric.fps",
    )

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("statsPanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.values: dict[str, QLabel] = {}
        self.labels: dict[str, QLabel] = {}
        for key in self.KEYS:
            card = QFrame()
            card.setObjectName("statCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            label = QLabel()
            label.setObjectName("muted")
            value = QLabel("—")
            value.setObjectName("statValue")
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            layout.addWidget(card, 1)
            self.labels[key] = label
            self.values[key] = value
        self.retranslate()

    def update_values(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            if key in self.values and self.values[key].text() != value:
                self.values[key].setText(value)

    def retranslate(self) -> None:
        for key, label in self.labels.items():
            label.setText(tr(key))
