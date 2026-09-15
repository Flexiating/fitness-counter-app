from PySide6.QtWidgets import QFrame,QVBoxLayout,QLabel
class DebugPanel(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("card"); layout=QVBoxLayout(self); layout.addWidget(QLabel("GỠ LỖI")); self.content=QLabel("Bật Chế độ gỡ lỗi để xem trạng thái, góc, ngưỡng, độ hiển thị, các lần lặp bị từ chối và điểm mốc."); self.content.setWordWrap(True); layout.addWidget(self.content)
