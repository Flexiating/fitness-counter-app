from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel


class CameraWidget(QLabel):
    def __init__(self) -> None:
        super().__init__("Camera preview will appear here")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(640, 360)
        self.setStyleSheet("background:#111827; color:#cbd5e1; border-radius:12px;")

    @Slot(QImage)
    def set_frame(self, image: QImage) -> None:
        self.setPixmap(QPixmap.fromImage(image).scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
