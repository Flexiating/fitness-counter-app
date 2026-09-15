from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.ui.workout_metrics import WorkoutSnapshot, speed_label


class WorkoutSummaryDialog(QDialog):
    new_session_requested = Signal()
    save_requested = Signal()

    def __init__(self, exercise: str, snapshot: WorkoutSnapshot, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Hoàn thành buổi tập")
        self.setModal(False)
        self.setMinimumWidth(500)
        root = QVBoxLayout(self)
        title = QLabel("HOÀN THÀNH BUỔI TẬP")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(exercise)
        subtitle.setObjectName("muted")
        root.addWidget(title)
        root.addWidget(subtitle)

        grid = QGridLayout()
        values = (
            ("Số lần", str(snapshot.repetitions)),
            ("Thời gian", f"{int(snapshot.duration)//60:02}:{int(snapshot.duration)%60:02}"),
            ("Tốc độ trung bình", speed_label(snapshot.average_rep_seconds)),
            ("Độ chính xác", f"{snapshot.accuracy:.0f}%"),
            ("Chuỗi tốt nhất", str(snapshot.best_streak)),
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
        self.new_session = QPushButton("Buổi tập mới")
        self.save = QPushButton("Lưu buổi tập")
        self.close_button = QPushButton("Đóng")
        self.new_session.clicked.connect(self.new_session_requested)
        self.save.clicked.connect(self.save_requested)
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.new_session)
        buttons.addWidget(self.save)
        buttons.addWidget(self.close_button)
        root.addLayout(buttons)

    def mark_saved(self) -> None:
        self.save.setText("Đã lưu")
        self.save.setEnabled(False)
