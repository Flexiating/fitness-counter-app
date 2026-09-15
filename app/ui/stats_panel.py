from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class StatsPanel(QFrame):
    LABELS = (
        "Số lần hôm nay",
        "Thời gian tập",
        "Tốc độ hiện tại",
        "Tốc độ trung bình",
        "Độ chính xác",
        "Chất lượng tư thế",
        "FPS",
    )

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("statsPanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.values: dict[str, QLabel] = {}
        for name in self.LABELS:
            card = QFrame()
            card.setObjectName("statCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            label = QLabel(name)
            label.setObjectName("muted")
            value = QLabel("—")
            value.setObjectName("statValue")
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            layout.addWidget(card, 1)
            self.values[name] = value

    def update_values(self, values: dict[str, str]) -> None:
        for name, value in values.items():
            if name in self.values and self.values[name].text() != value:
                self.values[name].setText(value)
