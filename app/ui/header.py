from datetime import datetime
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

class Header(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("card"); layout=QHBoxLayout(self)
        self.title=QLabel("Theo dõi luyện tập"); self.title.setStyleSheet("font-size:24px;font-weight:700;")
        self.meta=QLabel(); self.meta.setObjectName("muted"); layout.addWidget(self.title); layout.addStretch(); layout.addWidget(self.meta)
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(1000); self.refresh()
    def refresh(self): self.meta.setText(f"Camera • Mô hình sẵn sàng • {datetime.now():%H:%M}")
