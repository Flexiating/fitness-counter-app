from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.data.history import HistoryRepository, WorkoutSession
from app.ui.translations import tr, translate_exercise


class HistoryPage(QWidget):
    changed = Signal()

    def __init__(self, repository: HistoryRepository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self._sessions: list[WorkoutSession] = []
        root = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("placeholderTitle")
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.filter = QComboBox()
        self.delete = QPushButton()
        self.delete_all = QPushButton()
        self.export_csv = QPushButton()
        self.export_json = QPushButton()
        controls.addWidget(self.title)
        controls.addStretch()
        controls.addWidget(self.search)
        controls.addWidget(self.filter)
        controls.addWidget(self.delete)
        controls.addWidget(self.delete_all)
        controls.addWidget(self.export_csv)
        controls.addWidget(self.export_json)
        root.addLayout(controls)

        self.table = QTableWidget(0, 8)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        root.addWidget(self.table, 1)
        self.empty = QLabel()
        self.empty.setObjectName("muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.empty)

        self.search.textChanged.connect(self.refresh)
        self.filter.currentIndexChanged.connect(self.refresh)
        self.table.itemClicked.connect(lambda _item: self.open_selected())
        self.delete.clicked.connect(self.delete_selected)
        self.delete_all.clicked.connect(self.clear)
        self.export_csv.clicked.connect(lambda: self.export("csv"))
        self.export_json.clicked.connect(lambda: self.export("json"))
        self.retranslate()
        self.refresh()

    def retranslate(self) -> None:
        self.title.setText(tr("history.title"))
        self.search.setPlaceholderText(tr("history.search"))
        selected = self.filter.currentData()
        self.filter.blockSignals(True)
        self.filter.clear()
        self.filter.addItem(tr("history.filter_all"), None)
        self.filter.addItem(tr("exercise.push_up"), "push_up")
        self.filter.addItem(tr("exercise.crunch"), "crunch")
        index = self.filter.findData(selected)
        self.filter.setCurrentIndex(max(0, index))
        self.filter.blockSignals(False)
        self.delete.setText(tr("button.delete"))
        self.delete_all.setText(tr("button.delete_all"))
        self.export_csv.setText(tr("button.export_csv"))
        self.export_json.setText(tr("button.export_json"))
        self.empty.setText(tr("history.empty"))
        self.table.setHorizontalHeaderLabels([
            tr("history.date"), tr("history.start"), tr("history.exercise"),
            tr("history.reps"), tr("history.duration"), tr("history.avg_posture"),
            tr("history.avg_tracking"), tr("history.target"),
        ])
        self.refresh()

    def refresh(self) -> None:
        exercise = self.filter.currentData() if self.filter.count() else None
        self._sessions = self.repository.list(self.search.text(), exercise)
        self.table.setRowCount(len(self._sessions))
        for row, session in enumerate(self._sessions):
            started = datetime.fromisoformat(session.started_at)
            values = (
                started.strftime("%Y-%m-%d"), started.strftime("%H:%M:%S"),
                translate_exercise(session.exercise), str(session.total_reps),
                self._duration(session.duration_seconds), f"{session.average_posture_score:.0f}%",
                f"{session.average_tracking_confidence:.0f}%",
                tr("history.yes") if session.target_reached else tr("history.no"),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, session.id)
                self.table.setItem(row, column, item)
        self.empty.setVisible(not self._sessions)
        self.table.setVisible(bool(self._sessions))
        self.delete.setEnabled(bool(self._sessions))
        self.delete_all.setEnabled(bool(self.repository.list()))

    def selected_session(self) -> WorkoutSession | None:
        row = self.table.currentRow()
        return self._sessions[row] if 0 <= row < len(self._sessions) else None

    def open_selected(self) -> None:
        session = self.selected_session()
        if session is None:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("history.details"))
        form = QFormLayout(dialog)
        started, ended = datetime.fromisoformat(session.started_at), datetime.fromisoformat(session.ended_at)
        fields = (
            ("history.date", started.strftime("%Y-%m-%d")),
            ("history.start", started.strftime("%H:%M:%S")),
            ("history.end", ended.strftime("%H:%M:%S")),
            ("history.exercise", translate_exercise(session.exercise)),
            ("history.reps", str(session.total_reps)),
            ("history.duration", self._duration(session.duration_seconds)),
            ("history.avg_fps", f"{session.average_fps:.1f}"),
            ("history.avg_posture", f"{session.average_posture_score:.1f}%"),
            ("history.avg_tracking", f"{session.average_tracking_confidence:.1f}%"),
            ("history.best_posture", f"{session.best_posture_score:.1f}%"),
            ("history.target", tr("history.yes") if session.target_reached else tr("history.no")),
        )
        for key, value in fields:
            form.addRow(tr(key), QLabel(value))
        close = QPushButton(tr("button.close"))
        close.clicked.connect(dialog.accept)
        form.addRow(close)
        dialog.exec()

    def delete_selected(self) -> None:
        session = self.selected_session()
        if session is None or session.id is None:
            return
        if QMessageBox.question(self, tr("dialog.delete"), tr("history.delete_confirm")) == QMessageBox.StandardButton.Yes:
            self.repository.delete(session.id)
            self.refresh()
            self.changed.emit()

    def clear(self) -> None:
        if not self.repository.list():
            return
        if QMessageBox.question(self, tr("dialog.delete"), tr("history.delete_all_confirm")) == QMessageBox.StandardButton.Yes:
            self.repository.clear()
            self.refresh()
            self.changed.emit()

    def export(self, kind: str) -> None:
        suffix = "csv" if kind == "csv" else "json"
        file_filter = tr("history.csv_filter" if kind == "csv" else "history.json_filter")
        path, _ = QFileDialog.getSaveFileName(self, tr("dialog.history"), f"workout-history.{suffix}", file_filter)
        if not path:
            return
        try:
            getattr(self.repository, f"export_{kind}")(path, self._sessions)
        except OSError as exc:
            QMessageBox.warning(self, tr("dialog.export_failed"), str(exc))
        else:
            QMessageBox.information(self, tr("dialog.history"), tr("history.exported"))

    @staticmethod
    def _duration(seconds: float) -> str:
        value = max(0, int(seconds))
        return f"{value // 60:02}:{value % 60:02}"
