"""Presentation-only primitives shared by desktop screens (200 ms motion)."""
from PySide6.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation, QObject, QPropertyAnimation, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QPushButton, QStyle, QStyleOptionButton, QStylePainter, QTabBar,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QLabel, QProgressBar, QWidget, QFrame, QCheckBox,
)

ACCENT = "#2D8CFF"
SUCCESS = "#32D583"


def motion(parent, update):
    animation = QVariantAnimation(parent)
    animation.setDuration(200)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.valueChanged.connect(update)
    return animation


class Button(QPushButton):
    """Native button semantics with a painted lift; layout geometry stays stable."""
    def __init__(self, *args, shadow=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        self._lift = 0.0
        self._motion = motion(self, self._tick)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setColor(QColor(0, 0, 0, 65))
        self._shadow.setBlurRadius(8)
        self._shadow.setOffset(0, 2)
        if shadow:
            self.setGraphicsEffect(self._shadow)

    def _tick(self, value):
        self._lift = float(value)
        self._shadow.setBlurRadius(8 + self._lift * 5)
        self.update()

    def _animate(self, target):
        self._motion.stop()
        self._motion.setStartValue(self._lift)
        self._motion.setEndValue(target)
        self._motion.start()

    def enterEvent(self, event):
        self._animate(2.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        option = QStyleOptionButton()
        self.initStyleOption(option)
        painter = QStylePainter(self)
        painter.translate(self.width() / 2, self.height() / 2 - self._lift)
        scale = .98 if self.isDown() else 1.0
        painter.scale(scale, scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)


class AnimatedLabel(QLabel):
    """Animate numeric presentation without delaying the underlying label value."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._display = None
        self._motion = motion(self, self._tick)

    def _tick(self, value):
        self._display = float(value)
        self.update()

    def setText(self, text):
        old = self.text()
        super().setText(text)
        if old != text and text.isdigit() and old.isdigit():
            self._motion.stop()
            self._motion.setStartValue(self._display if self._display is not None else float(old))
            self._motion.setEndValue(float(text))
            self._motion.start()
        elif old != text:
            self._motion.stop()
            self._display = None

    def paintEvent(self, event):
        if self._display is None or not self._motion.state():
            return super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(self.palette().windowText().color())
        painter.setFont(self.font())
        painter.drawText(self.contentsRect(), self.alignment(), str(round(self._display)))


class ProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fraction = 0.0
        self._motion = motion(self, self._tick)

    def _tick(self, value):
        self._fraction = float(value)
        self.update()

    def setValue(self, value):
        super().setValue(value)
        target = max(0, (value - self.minimum()) / max(1, self.maximum() - self.minimum()))
        if self._motion.endValue() == target:
            return
        self._motion.stop()
        self._motion.setStartValue(self._fraction)
        self._motion.setEndValue(target)
        self._motion.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#292E3A"))
        painter.drawRoundedRect(rect, 4, 4)
        rect.setWidth(rect.width() * min(1.0, self._fraction))
        painter.setBrush(QColor(ACCENT))
        painter.drawRoundedRect(rect, 4, 4)


class ProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self._fraction = 0.0
        self._motion = motion(self, self._tick)

    def _tick(self, value):
        self._fraction = float(value)
        self.update()

    def set_progress(self, value):
        target = max(0.0, min(1.0, value))
        if self._motion.endValue() == target:
            return
        self._motion.stop()
        self._motion.setStartValue(self._fraction)
        self._motion.setEndValue(target)
        self._motion.start()
        self.setAccessibleName(f"{round(target * 100)}%")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        painter.setPen(QPen(QColor("#303744"), 5))
        painter.drawEllipse(rect)
        painter.setPen(QPen(QColor(SUCCESS if self._fraction >= 1 else ACCENT), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 90 * 16, -round(self._fraction * 360 * 16))
        painter.setPen(QColor("#F5F7FA"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{round(self._fraction * 100)}%")


class TabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._indicator = QRectF()
        self._motion = motion(self, self._tick)
        self.currentChanged.connect(self._move)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setExpanding(False)

    def _tick(self, value):
        self._indicator = value
        self.update()

    def _move(self, index):
        target = QRectF(self.tabRect(index))
        target.setTop(target.bottom() - 2)
        self._motion.stop()
        self._motion.setStartValue(self._indicator if not self._indicator.isNull() else target)
        self._motion.setEndValue(target)
        self._motion.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._move(self.currentIndex())

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self._indicator, QColor(ACCENT))


class ExerciseIllustration(QWidget):
    """Resolution-independent, deliberately simple instructional silhouettes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exercise = "push_up"
        self.setMinimumHeight(130)
        self.setMaximumHeight(180)

    def set_exercise(self, exercise):
        self.exercise = exercise
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2 - 160, 5)
        painter.setPen(QPen(QColor("#303744"), 2))
        painter.drawLine(10, 120, 310, 120)
        painter.setPen(QPen(QColor(ACCENT), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        points = [(70, 48), (135, 68), (260, 113)] if self.exercise == "push_up" else [(95, 70), (160, 112), (220, 58), (275, 114)]
        for a, b in zip(points, points[1:]):
            painter.drawLine(*a, *b)
        if self.exercise == "push_up":
            painter.drawLine(70, 48, 75, 114)
            painter.drawEllipse(42, 19, 26, 26)
        else:
            painter.drawLine(95, 70, 135, 57)
            painter.drawEllipse(63, 45, 26, 26)


class HoverFrame(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._glow = 0.0
        self._motion = motion(self, self._tick)

    def _tick(self, value):
        self._glow = float(value)
        self.update()

    def _animate(self, target):
        self._motion.stop()
        self._motion.setStartValue(self._glow)
        self._motion.setEndValue(target)
        self._motion.start()

    def enterEvent(self, event):
        self._animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.objectName() not in {"card", "miniCard", "statCard", "guideCard", "sidebarCard"}:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(ACCENT); color.setAlphaF(self._glow * .55)
        painter.setPen(QPen(color, 1.5)); painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 16, 16)


class CameraGlyph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._pulse = 1.0
        self._motion = motion(self, self._tick)

    def _tick(self, value):
        self._pulse = float(value)
        self.update()

    def set_loading(self, loading):
        self._motion.stop()
        self._pulse = 1.0
        if loading:
            self._motion.setStartValue(.4)
            self._motion.setEndValue(1.0)
            self._motion.setLoopCount(1)
            self._motion.start()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#A9B4C4"); color.setAlphaF(self._pulse)
        painter.setPen(QPen(color, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(7, 20, 50, 34), 8, 8)
        painter.drawEllipse(QRectF(23, 29, 18, 18))
        painter.drawLine(20, 20, 24, 12)
        painter.drawLine(24, 12, 40, 12)
        painter.drawLine(40, 12, 44, 20)


class PageTransition(QObject):
    """Fade a snapshot, rather than applying effects to a live video widget."""
    def __init__(self, tabs):
        super().__init__(tabs)
        self.tabs = tabs
        self.previous = tabs.currentWidget()
        self.cover = QLabel(tabs)
        self.cover.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.cover.hide()
        self.opacity = QGraphicsOpacityEffect(self.cover)
        self.cover.setGraphicsEffect(self.opacity)
        self.animation = QPropertyAnimation(self.opacity, b"opacity", self)
        self.animation.setDuration(200)
        self.animation.finished.connect(self.cover.hide)
        tabs.currentChanged.connect(self.change)

    def change(self, index):
        page = self.tabs.widget(index)
        if self.previous is not None and self.tabs.isVisible():
            self.animation.stop()
            self.cover.setPixmap(self.previous.grab())
            self.cover.setGeometry(page.geometry())
            self.opacity.setOpacity(1.0)
            self.cover.show(); self.cover.raise_()
            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.0)
            self.animation.start()
        self.previous = page


class Disclosure(QObject):
    def __init__(self, button, body):
        super().__init__(button)
        self.button, self.body = button, body
        self.animation = QPropertyAnimation(body, b"maximumHeight", self)
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self.finish)
        button.toggled.connect(self.toggle)

    def toggle(self, expanded):
        self.animation.stop()
        height = self.body.height() if self.body.isVisible() else 0
        self.body.show()
        self.animation.setStartValue(height)
        self.animation.setEndValue(max(self.body.sizeHint().height(), self.body.heightForWidth(self.body.width())) if expanded else 0)
        self.animation.start()

    def finish(self):
        self.body.setVisible(self.button.isChecked())
        if self.button.isChecked():
            self.body.setMaximumHeight(16777215)


class Switch(QCheckBox):
    """Animated switch retaining Qt check-box keyboard and accessibility behavior."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 0.0
        self._motion = motion(self, self._tick)
        self.toggled.connect(self._toggle)

    def _tick(self, value):
        self._position = float(value)
        self.update()

    def _toggle(self, checked):
        self._motion.stop()
        self._motion.setStartValue(self._position)
        self._motion.setEndValue(1.0 if checked else 0.0)
        self._motion.start()

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        top = (self.height() - 22) / 2
        painter.setPen(QPen(QColor("#B4D6FF" if self.hasFocus() else "#526074"), 1))
        painter.setBrush(QColor(ACCENT if self.isChecked() else "#303744"))
        painter.drawRoundedRect(QRectF(1, top, 38, 22), 11, 11)
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor("#F5F7FA"))
        painter.drawEllipse(QRectF(4 + 16 * self._position, top + 3, 16, 16))
        painter.setPen(QColor("#CFD6E1"))
        painter.drawText(self.rect().adjusted(50, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter, self.text())


class Toast(QLabel):
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setAccessibleName(text)
        self.setStyleSheet("background:#183627;color:#C5F8DD;border:1px solid #32D583;border-radius:12px;padding:14px 20px;")
        self.adjustSize()
        self.move(max(12, (parent.width() - self.width()) // 2), parent.height() - self.height() - 22)
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.animation = QPropertyAnimation(self.opacity, b"opacity", self)
        self.animation.setDuration(200); self.animation.setStartValue(0.0); self.animation.setEndValue(1.0)
        self.show(); self.raise_(); self.animation.start()
        QTimer.singleShot(2500, self.dismiss)

    def dismiss(self):
        self.animation.setStartValue(1.0); self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()
