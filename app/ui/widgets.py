from app.ui.design import AnimatedLabel as QLabel


def value_label(text: str, size: int = 18) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"font-size:{size}px; font-weight:600;")
    return label
