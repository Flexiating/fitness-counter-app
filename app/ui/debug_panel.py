from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from app.ui.translations import tr


class DebugPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        self.title = QLabel()
        layout.addWidget(self.title)
        self.angle_content = QLabel()
        self.exercise_content = QLabel()
        for label in (self.angle_content, self.exercise_content):
            label.setWordWrap(True)
            label.setObjectName("muted")
            layout.addWidget(label)
        self.retranslate()

    def retranslate(self) -> None:
        self.title.setText(tr("debug.console"))
        self.angle_content.setText(tr("debug.angles_empty"))
        self.exercise_content.setText(tr("debug.exercise_empty"))
