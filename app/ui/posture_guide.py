from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QVBoxLayout

from app.ui.translations import tr
from app.ui.design import Button, ExerciseIllustration, Disclosure
from app.ui.design import HoverFrame as QFrame


class PostureGuide(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("guidePage")
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 18, 8, 8)
        root.setSpacing(14)
        self.title = QLabel(); self.title.setObjectName("placeholderTitle")
        self.subtitle = QLabel(); self.subtitle.setObjectName("muted")
        self.selector = QComboBox(); self.selector.setMaximumWidth(280)
        self.selector.addItem("", "push_up"); self.selector.addItem("", "crunch")
        self.selector.currentIndexChanged.connect(self._selection_changed)
        root.addWidget(self.title); root.addWidget(self.subtitle); root.addWidget(self.selector)
        self.illustration = ExerciseIllustration()
        root.addWidget(self.illustration)

        grid = QGridLayout(); grid.setSpacing(14)
        self.first_card, first_layout, self.first_title = self._card()
        self.first = self._body(); first_layout.addWidget(self.first)
        self.second_card, second_layout, self.second_title = self._card()
        self.second = self._body(); second_layout.addWidget(self.second)
        self.mistakes_card, mistakes_layout, self.mistakes_title = self._card()
        self.mistakes = self._body(); mistakes_layout.addWidget(self.mistakes)
        self.tips_card, tips_layout, self.tips_title = self._card()
        self.tips = self._body(); tips_layout.addWidget(self.tips)
        grid.addWidget(self.first_card, 0, 0); grid.addWidget(self.second_card, 0, 1)
        grid.addWidget(self.mistakes_card, 1, 0); grid.addWidget(self.tips_card, 1, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        root.addLayout(grid, 1)
        for heading, body in ((self.first_title, self.first), (self.second_title, self.second), (self.mistakes_title, self.mistakes), (self.tips_title, self.tips)):
            heading.setCheckable(True)
            heading.setChecked(True)
            heading.disclosure = Disclosure(heading, body)
        self.retranslate()

    @staticmethod
    def _card() -> tuple[QFrame, QVBoxLayout, QLabel]:
        card = QFrame(); card.setObjectName("guideCard")
        layout = QVBoxLayout(card); heading = Button(); heading.setObjectName("sectionLabel")
        layout.setContentsMargins(20, 18, 20, 18)
        layout.addWidget(heading)
        return card, layout, heading

    @staticmethod
    def _body() -> QLabel:
        label = QLabel(); label.setWordWrap(True); label.setObjectName("guideText")
        return label

    def _selection_changed(self) -> None:
        self.set_exercise(str(self.selector.currentData()))

    def set_exercise(self, exercise: str) -> None:
        exercise = exercise if exercise in {"push_up", "crunch"} else "push_up"
        index = self.selector.findData(exercise)
        if index != self.selector.currentIndex():
            self.selector.blockSignals(True); self.selector.setCurrentIndex(index); self.selector.blockSignals(False)
        push_up = exercise == "push_up"
        self.illustration.set_exercise(exercise)
        self.first_title.setText(tr("guide.start" if push_up else "guide.posture"))
        self.second_title.setText(tr("guide.end" if push_up else "guide.range"))
        prefix = "guide.push" if push_up else "guide.crunch"
        self.first.setText(tr(f"{prefix}_{'start' if push_up else 'posture'}"))
        self.second.setText(tr(f"{prefix}_{'end' if push_up else 'range'}"))
        self.mistakes.setText(tr(f"{prefix}_mistakes")); self.tips.setText(tr(f"{prefix}_tips"))

    def retranslate(self) -> None:
        self.title.setText(tr("guide.title")); self.subtitle.setText(tr("guide.subtitle"))
        self.selector.setItemText(0, tr("exercise.push_up")); self.selector.setItemText(1, tr("exercise.crunch"))
        self.mistakes_title.setText(tr("guide.mistakes")); self.tips_title.setText(tr("guide.tips"))
        self.set_exercise(str(self.selector.currentData()))
