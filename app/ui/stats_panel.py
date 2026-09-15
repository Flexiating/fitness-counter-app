from PySide6.QtWidgets import QFrame,QHBoxLayout,QLabel,QVBoxLayout
class StatsPanel(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("card"); layout=QHBoxLayout(self)
        self.values={}
        for name in ("Số lần hôm nay","Thời gian tập","Calo","Tốc độ hiện tại","Tốc độ trung bình","Độ chính xác","Chất lượng tư thế"):
            card=QVBoxLayout(); label=QLabel(name); label.setObjectName("muted"); value=QLabel("—"); value.setStyleSheet("font-size:18px;font-weight:700;"); card.addWidget(label); card.addWidget(value); layout.addLayout(card); self.values[name]=value
