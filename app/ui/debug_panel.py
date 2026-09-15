from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class DebugPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("DEBUG CONSOLE"))
        self.angle_content = QLabel("Joint angles: no pose detected")
        self.exercise_content = QLabel("No exercise data")
        for label in (self.angle_content, self.exercise_content):
            label.setWordWrap(True)
            label.setObjectName("muted")
            layout.addWidget(label)
