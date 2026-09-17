from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout
from app.ui.design import Button as QPushButton

from app.ui.workout_metrics import WorkoutSnapshot, speed_label
from app.ui.translations import tr


class WorkoutSummaryDialog(QDialog):
    new_session_requested = Signal()

    def __init__(self, exercise: str, snapshot: WorkoutSnapshot, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dialog.completed"))
        self.setModal(False)
        self.setMinimumWidth(500)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)
        title = QLabel(tr("dialog.completed").upper())
        title.setObjectName("dialogTitle")
        subtitle = QLabel(exercise)
        subtitle.setObjectName("muted")
        root.addWidget(title)
        root.addWidget(subtitle)

        grid = QGridLayout()
        grid.setVerticalSpacing(18)
        values = (
            (tr("history.reps"), str(snapshot.repetitions)),
            (tr("history.duration"), f"{int(snapshot.duration)//60:02}:{int(snapshot.duration)%60:02}"),
            (tr("metric.average_speed"), speed_label(snapshot.average_rep_seconds)),
            (tr("metric.accuracy"), f"{snapshot.accuracy:.0f}%"),
            (tr("history.best_posture"), f"{snapshot.best_form_score:.0f}%"),
        )
        for index, (name, value) in enumerate(values):
            label = QLabel(name)
            label.setObjectName("muted")
            result = QLabel(value)
            result.setObjectName("summaryValue")
            grid.addWidget(label, index, 0)
            grid.addWidget(result, index, 1)
        root.addLayout(grid)

        buttons = QHBoxLayout()
        self.new_session = QPushButton(tr("button.new_session"))
        self.saved_label = QLabel(tr("button.saved"))
        self.saved_label.setObjectName("muted")
        self.close_button = QPushButton(tr("button.close"))
        self.new_session.clicked.connect(self.new_session_requested)
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.new_session)
        buttons.addWidget(self.saved_label)
        buttons.addWidget(self.close_button)
        root.addLayout(buttons)
