from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    CaptionLabel,
    BodyLabel,
    FluentIcon,
    AvatarWidget,
)

from src.core.interfaces import IMainInterface
from src.ui.interfaces.component import (
    HyperLinkCard,
    SwitchCard,
    SettingCardGroup,
)
from src.utils import get_base_path


class Logo(QWidget):
    def __init__(
        self,
        icon: str | QImage | QPixmap,
        title: str,
        description: str,
        parent: QWidget = None,
    ):
        super().__init__(parent)

        self.avatarWidget = AvatarWidget(icon, self)
        self.avatarWidget.setRadius(64)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(description, self)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")

        self.hBoxLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout()

        # 添加Logo，标题和描述
        self.vBoxLayout.addWidget(self.avatarWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        # 设置主布局
        self.setLayout(self.vBoxLayout)


class MainInterface(IMainInterface):
    enableChanged = Signal(bool)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", "-"))
        self.hBoxLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setContentsMargins(18, 20, 18, 20)

        self.setLayout(self.vBoxLayout)  # 设置主布局

    def init_ui(self):
        self.vBoxLayout.addWidget(
            Logo(
                str(get_base_path() / "resources" / "logo.png"),
                "WindowsSearchUtility",
                self.tr(
                    "A small tool that non-invasively replaces Windows Search with other tools."
                ),
                self,
            )
        )

        self.mainSettingCardGroup = SettingCardGroup("", self)

        self.enableCard = SwitchCard(
            QIcon(str(get_base_path() / "resources" / "logo.png")),
            self.tr("Enable WindowsSearchUtility"),
            parent=self.mainSettingCardGroup,  # "替换"
        )
        self.enableCard.valueChanged.connect(
            lambda _, enabled: self.enableChanged.emit(enabled)
        )

        self.githubCard = HyperLinkCard(
            FluentIcon.INFO,
            "https://github.com/Illustar0/WindowsSearchUtility",
            "Github",
            self.tr("About"),
            "Copyright © 2025 Illustar0. All rights reserved.",
            parent=self.mainSettingCardGroup,
        )

        self.mainSettingCardGroup.addSettingCards([self.enableCard, self.githubCard])
        self.vBoxLayout.addWidget(self.mainSettingCardGroup)

    def setEnable(self, enabled: bool):
        self.enableCard.setValue(enabled)
