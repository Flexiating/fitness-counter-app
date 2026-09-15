from PySide6.QtWidgets import QFrame,QVBoxLayout,QLabel
class TimerWidget(QFrame):
 def __init__(self):
  super().__init__(); self.setObjectName('card'); l=QVBoxLayout(self); t=QLabel('BUỔI TẬP'); t.setObjectName('muted'); self.value=QLabel('SẴN SÀNG'); self.value.setStyleSheet('font-size:36px;font-weight:700;'); l.addWidget(t); l.addWidget(self.value)
