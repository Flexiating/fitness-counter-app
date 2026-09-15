from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QProgressBar, QVBoxLayout


class WorkoutStatusPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("statusPanel")
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)

        self.form_card, form_layout = self._card("CHẤT LƯỢNG ĐỘNG TÁC")
        self.form_value = QLabel("—")
        self.form_value.setObjectName("scoreValue")
        self.form_grade = QLabel("Đang chờ")
        self.form_grade.setObjectName("muted")
        self.tracking = QProgressBar()
        self.tracking.setRange(0, 100)
        self.tracking.setTextVisible(True)
        form_layout.addWidget(self.form_value)
        form_layout.addWidget(self.form_grade)
        form_layout.addWidget(self.tracking)

        self.goal_card, goal_layout = self._card("MỤC TIÊU BUỔI TẬP")
        self.goal_value = QLabel("0 / 20 lần")
        self.goal_value.setObjectName("scoreValue")
        self.goal_progress = QProgressBar()
        self.goal_progress.setRange(0, 20)
        self.goal_progress.setValue(0)
        self.goal_progress.setTextVisible(False)
        self.current_set = QLabel("Hiệp 1 / 3")
        self.current_set.setObjectName("muted")
        goal_layout.addWidget(self.goal_value)
        goal_layout.addWidget(self.goal_progress)
        goal_layout.addWidget(self.current_set)

        self.coach_card, coach_layout = self._card("HUẤN LUYỆN VIÊN AI")
        self.coach = QLabel("Bật camera để bắt đầu")
        self.coach.setObjectName("coachMessage")
        self.coach.setWordWrap(True)
        self.coach.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        coach_layout.addWidget(self.coach, 1)

        layout.addWidget(self.form_card, 0, 0)
        layout.addWidget(self.goal_card, 0, 1)
        layout.addWidget(self.coach_card, 0, 2)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 2)

    @staticmethod
    def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("miniCard")
        layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setObjectName("sectionLabel")
        layout.addWidget(title_label)
        return card, layout

    def update_quality(self, score: float, tracking: float, grade: str, color: str) -> None:
        self.form_value.setText(f"{score:.0f}%")
        self.form_value.setStyleSheet(f"color:{color};")
        self.form_grade.setText(grade)
        self.tracking.setValue(round(tracking))
        self.tracking.setFormat(f"Theo dõi {tracking:.0f}%")

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
        self.goal_value.setText(f"{set_reps} / {target_reps} lần")
        self.current_set.setText(f"Hiệp {current_set} / {target_sets}")

    def set_coach(self, message: str, color: str = "#cbd5e1") -> None:
        self.coach.setText(message)
        self.coach.setStyleSheet(f"color:{color};")
