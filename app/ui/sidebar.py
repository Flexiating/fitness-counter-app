from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.ui.translations import translate_exercise


class Sidebar(QFrame):
    goals_changed = Signal(int, int)

    def __init__(self, exercises) -> None:
        super().__init__()
        self.setObjectName("sidebarCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(9)

        layout.addWidget(self._heading("BÀI TẬP"))
        self.selector = QComboBox()
        for key, name in exercises.items():
            self.selector.addItem(translate_exercise(name), key)
        layout.addWidget(self.selector)
        upcoming = QLabel("Sắp có: Squat · Plank · Lunge")
        upcoming.setObjectName("muted")
        layout.addWidget(upcoming)

        layout.addSpacing(8)
        layout.addWidget(self._heading("MỤC TIÊU"))
        goal_row = QHBoxLayout()
        self.target_reps = self._spinbox(1, 999, 20, " lần")
        self.target_sets = self._spinbox(1, 99, 3, " hiệp")
        goal_row.addWidget(self.target_reps)
        goal_row.addWidget(self.target_sets)
        layout.addLayout(goal_row)
        self.target_reps.valueChanged.connect(self._emit_goals)
        self.target_sets.valueChanged.connect(self._emit_goals)

        layout.addSpacing(8)
        layout.addWidget(self._heading("HẸN GIỜ BUỔI TẬP"))
        self.timer_enabled = QCheckBox("Bật hẹn giờ")
        self.timer_enabled.setChecked(True)
        layout.addWidget(self.timer_enabled)
        self.timer_mode = QComboBox()
        self.timer_mode.addItem("Bấm giờ", "stopwatch")
        self.timer_mode.addItem("Đếm ngược", "countdown")
        layout.addWidget(self.timer_mode)
        self.timer_duration = QComboBox()
        for seconds in (30, 60, 90, 120):
            self.timer_duration.addItem(f"{seconds} giây", seconds)
        self.timer_duration.addItem("Tùy chỉnh...", -1)
        layout.addWidget(self.timer_duration)
        self.custom_duration = self._spinbox(1, 3_600, 60, " giây")
        self.custom_duration.hide()
        layout.addWidget(self.custom_duration)
        self.timer_duration.currentIndexChanged.connect(self._duration_changed)
        self.apply_timer = QPushButton("Áp dụng hẹn giờ")
        layout.addWidget(self.apply_timer)

        self.debug_mode = QCheckBox("Chế độ gỡ lỗi")
        layout.addWidget(self.debug_mode)
        layout.addStretch()

        self.start = QPushButton("▶  Bật camera")
        self.start.setObjectName("primaryButton")
        self.stop = QPushButton("■  Tắt camera")
        self.reset = QPushButton("↻  Đặt lại bộ đếm")
        self.pause = QPushButton("Ⅱ  Tạm dừng")
        self.settings = QPushButton("⚙  Cài đặt")
        self.pause.setEnabled(False)
        for button in (self.start, self.stop, self.reset, self.pause, self.settings):
            layout.addWidget(button)

    @staticmethod
    def _heading(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    @staticmethod
    def _spinbox(minimum: int, maximum: int, value: int, suffix: str) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(minimum, maximum)
        widget.setValue(value)
        widget.setSuffix(suffix)
        return widget

    def selected_duration(self) -> int:
        selected = int(self.timer_duration.currentData())
        return self.custom_duration.value() if selected == -1 else selected

    def _duration_changed(self) -> None:
        self.custom_duration.setVisible(self.timer_duration.currentData() == -1)

    def _emit_goals(self) -> None:
        self.goals_changed.emit(self.target_reps.value(), self.target_sets.value())
