from PySide6.QtWidgets import QLabel


def value_label(text: str, size: int = 18) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"font-size:{size}px; font-weight:600; color:#e2e8f0;")
    return label
