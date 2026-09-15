from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QComboBox, QPushButton, QCheckBox
from app.ui.translations import translate_exercise

class Sidebar(QFrame):
    def __init__(self, exercises):
        super().__init__(); self.setObjectName("card"); layout=QVBoxLayout(self); layout.addWidget(QLabel("BÀI TẬP"))
        self.selector=QComboBox()
        for key,name in exercises.items(): self.selector.addItem(translate_exercise(name),key)
        layout.addWidget(self.selector); layout.addWidget(QLabel("Sắp có: Squat • Plank • Lunge"))
        layout.addWidget(QLabel("HẸN GIỜ BUỔI TẬP")); self.timer_enabled=QCheckBox("Bật hẹn giờ"); self.timer_enabled.setChecked(True); layout.addWidget(self.timer_enabled)
        self.timer_mode=QComboBox(); self.timer_mode.addItem("Bấm giờ", "stopwatch"); self.timer_mode.addItem("Đếm ngược", "countdown"); layout.addWidget(self.timer_mode)
        self.timer_duration=QComboBox()
        for seconds in (30,45,60,90,120,180,300): self.timer_duration.addItem(f"{seconds} giây", seconds)
        layout.addWidget(self.timer_duration); self.apply_timer=QPushButton("Áp dụng hẹn giờ"); layout.addWidget(self.apply_timer); layout.addStretch()
        self.start=QPushButton("Bật camera"); self.stop=QPushButton("Tắt camera"); self.reset=QPushButton("Đặt lại bộ đếm"); self.pause=QPushButton("Tạm dừng"); self.settings=QPushButton("Cài đặt")
        for button in (self.start,self.stop,self.reset,self.pause,self.settings): layout.addWidget(button)
