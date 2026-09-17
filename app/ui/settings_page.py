from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QSpinBox, QVBoxLayout, QWidget,
)

from app.config.settings import SETTINGS, SettingsStore
from app.ui.translations import tr
from app.ui.design import Button as QPushButton
from app.ui.design import HoverFrame as QFrame
from app.ui.design import Switch as QCheckBox


class SettingsPage(QWidget):
    language_changed = Signal(str)
    theme_changed = Signal(bool)
    export_csv_requested = Signal()
    export_json_requested = Signal()
    delete_history_requested = Signal()

    def __init__(self, store: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.store = store
        root = QVBoxLayout(self)
        self.title = QLabel()
        self.title.setObjectName("placeholderTitle")
        root.addWidget(self.title)
        columns = QHBoxLayout()
        left, right = QVBoxLayout(), QVBoxLayout()
        columns.addLayout(left, 1)
        columns.addLayout(right, 1)
        root.addLayout(columns)

        self.appearance, appearance = self._section()
        self.dark_mode = QCheckBox()
        self.dark_mode.setChecked(True)
        self.dark_mode.setEnabled(False)
        self.language = QComboBox()
        self.language.addItem("English", "en")
        self.language.addItem("Tiếng Việt", "vi")
        self.language.setCurrentIndex(max(0, self.language.findData(SETTINGS.language)))
        appearance.addRow(self.dark_mode)
        self.language_label = QLabel()
        appearance.addRow(self.language_label, self.language)
        left.addWidget(self.appearance)

        self.camera, camera = self._section()
        self.camera_index = self._spin(0, 16, SETTINGS.camera_index)
        self.resolution = QComboBox()
        for width, height in ((640, 480), (960, 540), (1280, 720), (1920, 1080)):
            self.resolution.addItem(f"{width} × {height}", (width, height))
        current_resolution = self.resolution.findData((SETTINGS.camera_width, SETTINGS.camera_height))
        self.resolution.setCurrentIndex(max(0, current_resolution))
        self.fps = self._spin(1, 120, SETTINGS.target_fps)
        self.camera_index_label, self.resolution_label, self.fps_label = QLabel(), QLabel(), QLabel()
        camera.addRow(self.camera_index_label, self.camera_index)
        camera.addRow(self.resolution_label, self.resolution)
        camera.addRow(self.fps_label, self.fps)
        left.addWidget(self.camera)

        self.ai, ai = self._section()
        self.confidence = self._double(0.1, 1.0, SETTINGS.pose_min_confidence)
        self.tracking = self._double(0.1, 1.0, SETTINGS.pose_tracking_confidence)
        self.smoothing = self._spin(1, 30, SETTINGS.smoothing_window)
        self.confidence_label, self.tracking_label, self.smoothing_label = QLabel(), QLabel(), QLabel()
        ai.addRow(self.confidence_label, self.confidence)
        ai.addRow(self.tracking_label, self.tracking)
        ai.addRow(self.smoothing_label, self.smoothing)
        right.addWidget(self.ai)

        self.history, history = self._section()
        buttons = QVBoxLayout()
        self.export_csv, self.export_json, self.delete_history = QPushButton(), QPushButton(), QPushButton()
        buttons.addWidget(self.export_csv); buttons.addWidget(self.export_json); buttons.addWidget(self.delete_history)
        history.addRow(buttons)
        right.addWidget(self.history)

        self.about, about = self._section()
        self.version_label, self.build_label = QLabel(), QLabel()
        about.addRow(self.version_label, QLabel("2.1.1"))
        about.addRow(self.build_label, QLabel("2"))
        right.addWidget(self.about)
        self.note = QLabel()
        self.note.setObjectName("muted")
        self.note.setWordWrap(True)
        root.addWidget(self.note)
        root.addStretch()

        self.dark_mode.toggled.connect(self._theme_changed)
        self.language.currentIndexChanged.connect(self._language_changed)
        for widget in (self.camera_index, self.resolution, self.fps, self.confidence, self.tracking, self.smoothing):
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self._save)
            else:
                widget.valueChanged.connect(self._save)
        self.export_csv.clicked.connect(self.export_csv_requested)
        self.export_json.clicked.connect(self.export_json_requested)
        self.delete_history.clicked.connect(self.delete_history_requested)
        self.retranslate()

    @staticmethod
    def _section() -> tuple[QFrame, QFormLayout]:
        frame = QFrame()
        frame.setObjectName("card")
        form = QFormLayout(frame)
        form.setContentsMargins(24, 22, 24, 22)
        form.setVerticalSpacing(16)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        heading = QLabel()
        heading.setObjectName("sectionLabel")
        form.addRow(heading)
        frame._heading = heading  # type: ignore[attr-defined]
        return frame, form

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox(); spin.setRange(minimum, maximum); spin.setValue(value)
        return spin

    @staticmethod
    def _double(minimum: float, maximum: float, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(); spin.setRange(minimum, maximum); spin.setSingleStep(.05); spin.setDecimals(2); spin.setValue(value)
        return spin

    def _save(self, *_args) -> None:
        width, height = self.resolution.currentData()
        self.store.update(
            camera_index=self.camera_index.value(), camera_width=width, camera_height=height,
            target_fps=self.fps.value(), pose_min_confidence=self.confidence.value(),
            pose_tracking_confidence=self.tracking.value(), min_visibility=self.tracking.value(),
            smoothing_window=self.smoothing.value(),
        )

    def _theme_changed(self, checked: bool) -> None:
        self.store.update(dark_mode=checked)
        self.theme_changed.emit(checked)

    def _language_changed(self) -> None:
        language = str(self.language.currentData())
        self.store.update(language=language)
        self.language_changed.emit(language)

    def retranslate(self) -> None:
        self.title.setText(tr("settings.title"))
        self.appearance._heading.setText(tr("settings.appearance"))  # type: ignore[attr-defined]
        self.camera._heading.setText(tr("settings.camera"))  # type: ignore[attr-defined]
        self.ai._heading.setText(tr("settings.ai"))  # type: ignore[attr-defined]
        self.history._heading.setText(tr("settings.history"))  # type: ignore[attr-defined]
        self.about._heading.setText(tr("settings.about"))  # type: ignore[attr-defined]
        self.dark_mode.setText(tr("settings.dark_mode"))
        self.language_label.setText(tr("settings.language"))
        self.language.setItemText(0, tr("settings.english")); self.language.setItemText(1, tr("settings.vietnamese"))
        self.camera_index_label.setText(tr("settings.camera_index"))
        self.resolution_label.setText(tr("settings.resolution"))
        self.fps_label.setText(tr("settings.fps_limit"))
        self.confidence_label.setText(tr("settings.confidence"))
        self.tracking_label.setText(tr("settings.tracking"))
        self.smoothing_label.setText(tr("settings.smoothing"))
        self.export_csv.setText(tr("button.export_csv")); self.export_json.setText(tr("button.export_json")); self.delete_history.setText(tr("button.delete_all"))
        self.version_label.setText(tr("settings.version")); self.build_label.setText(tr("settings.build"))
        self.note.setText(tr("settings.restart_camera"))
