from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class PostureGuide(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("card")
        layout = QVBoxLayout(self)
        title = QLabel("HƯỚNG DẪN TƯ THẾ"); title.setStyleSheet("font-weight:700;")
        self.content = QLabel(); self.content.setWordWrap(True); self.content.setObjectName("muted")
        layout.addWidget(title); layout.addWidget(self.content)
        self.set_exercise("push_up")

    def set_exercise(self, exercise: str) -> None:
        if exercise == "crunch":
            self.content.setText("• Nằm nghiêng so với camera\n• Giữ cả vai, hông và đầu gối trong khung hình\n• Bắt đầu ở tư thế duỗi, rồi cuộn vai về phía đầu gối\n• Tránh ngồi hoặc đứng giữa các lần lặp")
        else:
            self.content.setText("• Đứng nghiêng so với camera\n• Giữ vai, khuỷu tay, cổ tay, hông và đầu gối trong khung hình\n• Giữ plank thẳng; tránh nâng hoặc hạ hông\n• Hạ người có kiểm soát, sau đó duỗi thẳng hoàn toàn")
