from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    CardWidget,
    FluentIconBase,
    BodyLabel,
    CaptionLabel,
    IconWidget,
)


class BaseCard(CardWidget):
    def __init__(self, title: str, content: str, icon: FluentIconBase, parent=None):
        super().__init__(parent)

        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content, self)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.iconWidget = IconWidget(icon, self)
        self.iconWidget.setFixedSize(24, 24)

        self.hBoxLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.setLayout(self.hBoxLayout)
        self.setFixedHeight(73)

        self.hBoxLayout.setContentsMargins(20, 10, 10, 10)
        self.hBoxLayout.setSpacing(15)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addStretch(1)
