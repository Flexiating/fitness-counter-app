from PySide6.QtWidgets import QFrame,QVBoxLayout,QLabel
from app.ui.translations import tr
class TimerWidget(QFrame):
 def __init__(self):
  super().__init__(); self.setObjectName('card'); l=QVBoxLayout(self); self.title=QLabel(); self.title.setObjectName('muted'); self.value=QLabel(); self.value.setStyleSheet('font-size:36px;font-weight:700;'); l.addWidget(self.title); l.addWidget(self.value); self.retranslate()
 def retranslate(self):
  self.title.setText(tr('tab.workout').upper()); self.value.setText(tr('state.ready'))
