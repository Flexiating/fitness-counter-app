from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QVBoxLayout


class PostureGuide(QFrame):
    _GUIDES = {
        "push_up": {
            "posture": (
                "• Đặt camera ngang thân người và đứng nghiêng so với camera.\n"
                "• Cổ tay nằm dưới vai, chân duỗi thẳng và siết cơ bụng.\n"
                "• Giữ vai, hông và gót chân gần như trên một đường thẳng.\n"
                "• Hạ ngực có kiểm soát rồi duỗi thẳng khuỷu tay."
            ),
            "mistakes": (
                "• Nâng hoặc võng hông quá nhiều.\n"
                "• Chỉ hạ nửa biên độ.\n"
                "• Xòe khuỷu tay quá xa thân người.\n"
                "• Để cổ tay hoặc khuỷu tay ra ngoài khung hình."
            ),
            "tips": (
                "Giữ nhịp thở đều: hít vào khi hạ xuống, thở ra khi đẩy lên. "
                "Nếu hệ thống mất theo dõi, hãy lùi camera xa hơn và tăng ánh sáng."
            ),
        },
        "crunch": {
            "posture": (
                "• Đặt camera ngang thân và nằm nghiêng so với camera.\n"
                "• Co đầu gối, đặt bàn chân chắc trên sàn và giữ lưng dưới ổn định.\n"
                "• Cuộn vai về phía đầu gối bằng cơ bụng, không kéo cổ.\n"
                "• Trở về tư thế duỗi có kiểm soát sau mỗi lần."
            ),
            "mistakes": (
                "• Ngồi bật dậy thay vì cuộn thân.\n"
                "• Dùng tay kéo đầu hoặc cổ.\n"
                "• Thực hiện biên độ quá ngắn.\n"
                "• Để vai, hông hoặc đầu gối ra ngoài khung hình."
            ),
            "tips": (
                "Thở ra khi cuộn người lên và giữ chuyển động chậm, đều. "
                "Camera cần nhìn rõ mũi, vai, hông và đầu gối trong toàn bộ lần lặp."
            ),
        },
    }

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("guidePage")
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 18, 8, 8)
        root.setSpacing(14)

        title = QLabel("HƯỚNG DẪN TƯ THẾ")
        title.setObjectName("placeholderTitle")
        subtitle = QLabel("Chọn bài tập để xem tư thế đúng và cách camera theo dõi tốt nhất.")
        subtitle.setObjectName("muted")
        self.selector = QComboBox()
        self.selector.addItem("Chống đẩy", "push_up")
        self.selector.addItem("Gập bụng", "crunch")
        self.selector.setMaximumWidth(280)
        self.selector.currentIndexChanged.connect(self._selection_changed)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(self.selector)

        grid = QGridLayout()
        grid.setSpacing(14)
        posture_card, posture_layout = self._card("TƯ THẾ ĐÚNG")
        self.content = self._body_label()
        posture_layout.addWidget(self.content)
        mistakes_card, mistakes_layout = self._card("LỖI THƯỜNG GẶP")
        self.mistakes = self._body_label()
        mistakes_layout.addWidget(self.mistakes)
        illustration_card, illustration_layout = self._card("MINH HỌA ĐỘNG TÁC")
        self.illustration = QLabel("▶\nMinh họa chuyển động đang được hoàn thiện")
        self.illustration.setObjectName("guideIllustration")
        self.illustration.setAlignment(Qt.AlignmentFlag.AlignCenter)
        illustration_layout.addWidget(self.illustration, 1)
        tips_card, tips_layout = self._card("MẸO LUYỆN TẬP")
        self.tips = self._body_label()
        tips_layout.addWidget(self.tips)
        faq_card, faq_layout = self._card("CÂU HỎI THƯỜNG GẶP")
        self.faq = self._body_label()
        self.faq.setText(
            "Vì sao hệ thống chưa đếm?\n"
            "Hãy kiểm tra ánh sáng, góc camera và đảm bảo các khớp cần thiết nằm trong khung hình.\n\n"
            "Tôi nên đặt camera cách bao xa?\n"
            "Đặt đủ xa để toàn bộ cơ thể và phạm vi chuyển động luôn hiển thị."
        )
        faq_layout.addWidget(self.faq)

        grid.addWidget(posture_card, 0, 0)
        grid.addWidget(mistakes_card, 0, 1)
        grid.addWidget(illustration_card, 1, 0)
        grid.addWidget(tips_card, 1, 1)
        grid.addWidget(faq_card, 2, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        root.addLayout(grid, 1)
        self.set_exercise("push_up")

    @staticmethod
    def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("guideCard")
        layout = QVBoxLayout(card)
        heading = QLabel(title)
        heading.setObjectName("sectionLabel")
        layout.addWidget(heading)
        return card, layout

    @staticmethod
    def _body_label() -> QLabel:
        label = QLabel()
        label.setWordWrap(True)
        label.setObjectName("guideText")
        label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        return label

    def _selection_changed(self) -> None:
        self.set_exercise(str(self.selector.currentData()))

    def set_exercise(self, exercise: str) -> None:
        exercise = exercise if exercise in self._GUIDES else "push_up"
        index = self.selector.findData(exercise)
        if index >= 0 and index != self.selector.currentIndex():
            self.selector.blockSignals(True)
            self.selector.setCurrentIndex(index)
            self.selector.blockSignals(False)
        guide = self._GUIDES[exercise]
        self.content.setText(guide["posture"])
        self.mistakes.setText(guide["mistakes"])
        self.tips.setText(guide["tips"])
