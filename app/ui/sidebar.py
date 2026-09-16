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

from app.ui.translations import tr, translate_exercise


class Sidebar(QFrame):
    goals_changed = Signal(int, int)

    def __init__(self, exercises) -> None:
        super().__init__()
        self.setObjectName("sidebarCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(9)

        self.exercise_heading = self._heading("")
        layout.addWidget(self.exercise_heading)
        self.selector = QComboBox()
        for key, name in exercises.items():
            self.selector.addItem(translate_exercise(name), key)
        layout.addWidget(self.selector)
        layout.addSpacing(8)
        self.goal_heading = self._heading("")
        layout.addWidget(self.goal_heading)
        goal_row = QHBoxLayout()
        self.target_reps = self._spinbox(1, 999, 20, "")
        self.target_sets = self._spinbox(1, 99, 3, "")
        goal_row.addWidget(self.target_reps)
        goal_row.addWidget(self.target_sets)
        layout.addLayout(goal_row)
        self.target_reps.valueChanged.connect(self._emit_goals)
        self.target_sets.valueChanged.connect(self._emit_goals)

        layout.addSpacing(8)
        self.timer_heading = self._heading("")
        layout.addWidget(self.timer_heading)
        self.timer_enabled = QCheckBox()
        self.timer_enabled.setChecked(True)
        layout.addWidget(self.timer_enabled)
        self.timer_mode = QComboBox()
        self.timer_mode.addItem("", "stopwatch")
        self.timer_mode.addItem("", "countdown")
        layout.addWidget(self.timer_mode)
        self.timer_duration = QComboBox()
        for seconds in (30, 60, 90, 120):
            self.timer_duration.addItem("", seconds)
        self.timer_duration.addItem("", -1)
        layout.addWidget(self.timer_duration)
        self.custom_duration = self._spinbox(1, 3_600, 60, "")
        self.custom_duration.hide()
        layout.addWidget(self.custom_duration)
        self.timer_duration.currentIndexChanged.connect(self._duration_changed)
        self.apply_timer = QPushButton()
        layout.addWidget(self.apply_timer)

        self.debug_mode = QCheckBox()
        layout.addWidget(self.debug_mode)
        layout.addStretch()

        self.start = QPushButton()
        self.start.setObjectName("primaryButton")
        self.stop = QPushButton()
        self.reset = QPushButton()
        self.pause = QPushButton()
        self.settings = QPushButton()
        self.pause.setEnabled(False)
        for button in (self.start, self.stop, self.reset, self.pause, self.settings):
            layout.addWidget(button)
        self.retranslate()

    def retranslate(self) -> None:
        self.exercise_heading.setText(tr("exercise.label"))
        for index in range(self.selector.count()):
            self.selector.setItemText(index, translate_exercise(str(self.selector.itemData(index))))
        self.goal_heading.setText(tr("goal.label"))
        self.target_reps.setSuffix(tr("goal.reps_suffix")); self.target_sets.setSuffix(tr("goal.sets_suffix"))
        self.timer_heading.setText(tr("timer.label")); self.timer_enabled.setText(tr("timer.enabled"))
        self.timer_mode.setItemText(0, tr("timer.stopwatch")); self.timer_mode.setItemText(1, tr("timer.countdown"))
        for index in range(self.timer_duration.count()):
            seconds = self.timer_duration.itemData(index)
            self.timer_duration.setItemText(index, tr("timer.custom") if seconds == -1 else tr("timer.seconds", seconds=seconds))
        self.custom_duration.setSuffix(" " + tr("timer.seconds", seconds="").strip())
        self.apply_timer.setText(tr("timer.apply")); self.debug_mode.setText(tr("debug.mode"))
        self.start.setText(tr("button.start_camera")); self.stop.setText(tr("button.stop_camera"))
        self.reset.setText(tr("button.reset")); self.pause.setText(tr("button.pause")); self.settings.setText(tr("button.settings"))

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
