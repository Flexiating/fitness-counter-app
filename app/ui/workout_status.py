from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout
from app.ui.design import ProgressBar as QProgressBar, ProgressRing
from app.ui.design import HoverFrame as QFrame
from app.ui.translations import tr


class WorkoutStatusPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("statusPanel")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)

        self.form_card, form_layout, self.form_title = self._card()
        self.form_value = QLabel("—")
        self.form_value.setObjectName("scoreValue")
        self.form_grade = QLabel()
        self.form_grade.setObjectName("muted")
        self.tracking = QProgressBar()
        self.tracking.setRange(0, 100)
        self.tracking.setTextVisible(True)
        form_layout.addWidget(self.form_value)
        form_layout.addWidget(self.form_grade)
        form_layout.addWidget(self.tracking)

        self.goal_card, goal_layout, self.goal_title = self._card()
        self.goal_value = QLabel()
        self.goal_value.setObjectName("scoreValue")
        self.goal_progress = QProgressBar()
        self.goal_progress.setRange(0, 20)
        self.goal_progress.setValue(0)
        self.goal_progress.setTextVisible(False)
        self.current_set = QLabel()
        self.current_set.setObjectName("muted")
        goal_layout.addWidget(self.goal_value)
        goal_layout.addWidget(self.goal_progress)
        goal_layout.addWidget(self.current_set)
        self.ring = ProgressRing()
        goal_layout.addWidget(self.ring, alignment=Qt.AlignmentFlag.AlignRight)

        self.coach_card, coach_layout, self.coach_title = self._card()
        self.coach = QLabel()
        self.coach.setObjectName("coachMessage")
        self.coach.setWordWrap(True)
        self.coach.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        coach_layout.addWidget(self.coach, 1)

        layout.addWidget(self.coach_card, 0, 0)
        layout.addWidget(self.goal_card, 1, 0)
        layout.addWidget(self.form_card, 2, 0)
        layout.setRowStretch(0, 1)
        layout.setVerticalSpacing(14)
        self.retranslate()

    @staticmethod
    def _card() -> tuple[QFrame, QVBoxLayout, QLabel]:
        card = QFrame()
        card.setObjectName("miniCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        title_label = QLabel()
        title_label.setObjectName("sectionLabel")
        layout.addWidget(title_label)
        return card, layout, title_label

    def update_quality(self, score: float, tracking: float, grade: str, color: str) -> None:
        self.form_value.setText(f"{score:.0f}%")
        self.form_value.setStyleSheet(f"color:{color};")
        self.form_grade.setText(grade)
        self.tracking.setValue(round(tracking))
        self.tracking.setFormat(tr("metric.tracking", value=f"{tracking:.0f}"))

    def update_goal(self, repetitions: int, target_reps: int, target_sets: int) -> None:
        target_reps = max(1, target_reps)
        target_sets = max(1, target_sets)
        total_target = target_reps * target_sets
        completed = min(repetitions, total_target)
        current_set = min(completed // target_reps + 1, target_sets)
        set_reps = completed % target_reps
        if completed == total_target:
            current_set, set_reps = target_sets, target_reps
        self.goal_progress.setRange(0, target_reps)
        self.goal_progress.setValue(set_reps)
        self.goal_value.setText(tr("goal.progress", current=set_reps, target=target_reps))
        self.current_set.setText(tr("goal.set", current=current_set, target=target_sets))
        self.ring.set_progress(completed / total_target)

    def set_coach(self, message: str, color: str = "#cbd5e1") -> None:
        self.coach.setText(message)
        self.coach.setStyleSheet(f"color:{color};")

    def retranslate(self) -> None:
        self.form_title.setText(tr("quality.title"))
        self.goal_title.setText(tr("target.title"))
        self.coach_title.setText(tr("coach.title"))
        if not self.form_grade.text() or self.form_grade.text() in {"Đang chờ", "Ready"}:
            self.form_grade.setText(tr("quality.waiting"))
        if not self.coach.text() or self.coach.text() in {"Bật camera để bắt đầu", "Start the camera to begin"}:
            self.coach.setText(tr("coach.start_camera"))
