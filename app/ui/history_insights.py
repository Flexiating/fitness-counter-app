"""Read-only history presentation; no persistence or workout state changes."""
from datetime import date, datetime, timedelta
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from app.ui.design import HoverFrame, motion
from app.ui.translations import tr


class ActivityChart(QWidget):
    def __init__(self):
        super().__init__()
        self.days = []
        self.values = []
        self._reveal = 1.0
        self._motion = motion(self, self._tick)
        self.setMinimumHeight(100)

    def _tick(self, value):
        self._reveal = float(value)
        self.update()

    def set_data(self, days, values):
        changed = self.values != values
        self.days, self.values = days, values
        self.setAccessibleName(tr("ui.weekly_activity"))
        self.setAccessibleDescription("; ".join(f"{day}: {tr('metric.reps', value=value)}" for day, value in zip(days, values)))
        self.setToolTip(self.accessibleDescription())
        if changed:
            self._motion.stop(); self._motion.setStartValue(0.0); self._motion.setEndValue(1.0); self._motion.start()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        peak = max(self.values, default=0) or 1
        width = self.width() / 7
        for index, (day, count) in enumerate(zip(self.days, self.values)):
            height = max(3, (self.height() - 40) * count / peak * self._reveal)
            x = index * width
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#2D8CFF" if count else "#303744"))
            painter.drawRoundedRect(QRectF(x + width * .3, self.height() - 23 - height, width * .4, height), 4, 4)
            painter.setPen(QColor("#A9B4C4"))
            painter.drawText(QRectF(x, self.height() - 20, width, 18), Qt.AlignmentFlag.AlignCenter, day.strftime("%d/%m"))
            painter.drawText(QRectF(x, self.height() - 42 - height, width, 18), Qt.AlignmentFlag.AlignCenter, str(count))


class HistoryInsights(QWidget):
    def __init__(self):
        super().__init__()
        root = QHBoxLayout(self); root.setContentsMargins(0, 8, 0, 8); root.setSpacing(14)
        self.weekly_title, self.best_title, self.streak_title = QLabel(), QLabel(), QLabel()
        self.chart = ActivityChart()
        self.best, self.streak = QLabel(), QLabel()
        for heading, value, stretch in ((self.weekly_title, self.chart, 3), (self.best_title, self.best, 1), (self.streak_title, self.streak, 1)):
            card = HoverFrame(); card.setObjectName("statCard")
            layout = QVBoxLayout(card); layout.setContentsMargins(20, 16, 20, 16)
            heading.setObjectName("muted"); heading.setWordWrap(True)
            value.setObjectName("statValue")
            layout.addWidget(heading); layout.addWidget(value)
            root.addWidget(card, stretch)

    def refresh(self, sessions):
        today = date.today()
        days = [today - timedelta(days=6 - index) for index in range(7)]
        totals = {}
        for session in sessions:
            day = datetime.fromisoformat(session.started_at).date()
            totals[day] = totals.get(day, 0) + session.total_reps
        self.chart.set_data(days, [totals.get(day, 0) for day in days])
        streak, day = 0, today if today in totals else today - timedelta(days=1)
        while day in totals:
            streak += 1; day -= timedelta(days=1)
        self.weekly_title.setText(tr("ui.weekly_activity"))
        self.best_title.setText(tr("ui.personal_best")); self.streak_title.setText(tr("ui.streak"))
        self.best.setText(tr("metric.reps", value=max((s.total_reps for s in sessions), default=0)))
        self.streak.setText(tr("ui.day" if streak == 1 else "ui.days", value=streak))
