from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    CaptionLabel,
    BodyLabel,
    FluentIcon,
    AvatarWidget,
    HyperlinkButton,
    FluentIconBase,
    PushButton,
    SwitchButton,
)

from .base import BaseCard


class Logo(QWidget):
    def __init__(self, icon, title, description, parent=None):
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


class AboutCard(BaseCard):
    """About Card"""

    def __init__(
        self,
        title: str,
        content: str,
        button_title,
        button_url,
        icon: FluentIconBase,
    ):
        super().__init__(title, content, icon)
        self.hBoxLayout.addWidget(
            HyperlinkButton(FluentIcon.LINK, button_url, button_title)
        )
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)


class VersionCard(BaseCard):
    """Version Update Card"""

    def __init__(
        self,
        title: str,
        content: str,
        button_title,
        icon: FluentIcon,
        on_check_update=None,
    ):
        super().__init__(title, content, icon)
        self.checkUpdateButton = PushButton(button_title, self)
        self.hBoxLayout.addWidget(self.checkUpdateButton)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        if on_check_update:
            self.checkUpdateButton.clicked.connect(on_check_update)


class EnableCard(BaseCard):
    """Function Setting Card"""

    enable = Signal(bool)

    def __init__(
        self,
        title: str,
        content: str,
        icon: FluentIcon,
        default_value: bool,
    ):
        super().__init__(title, content, icon)
        # 创建快捷键编辑器

        self.switchButton = SwitchButton(self)
        self.switchButton.setChecked(default_value)
        self.switchButton.checkedChanged.connect(self.enable)
        self.hBoxLayout.addWidget(self.switchButton)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)


class MainInterface(QWidget):
    def __init__(self, title: str, version: str, parent=None):
        super().__init__(parent)
        self.on_check_update_button_clicked = None  # 只是为了去除警告 （
        self.setObjectName(title.replace(" ", "-"))
        self.hBoxLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setContentsMargins(
            10, 20, 10, 20
        )  # 设置顶部边距为 20 像素，两侧边距为 10 像素

        self.setLayout(self.vBoxLayout)  # 设置主布局
        self.vBoxLayout.addWidget(
            Logo(
                "./resources/logo.png",
                "PowerToysRunEnhance",
                self.tr(
                    "A non-intrusive tool that replaces Windows Search with PowerToys Run"
                ),  # "一款非侵入式将 Windows Search 替换为 PowerToys Run 的小工具"
                self,
            )
        )

        # 添加弹簧，将 AboutCard 推到底部
        self.vBoxLayout.addStretch()
        # 添加 EnableCard
        # 暴露 EnableCard
        self.enableCard = EnableCard(
            self.tr("Replace"),  # "替换"
            self.tr(
                "Whether to replace Windows Search with PowerToys Run"
            ),  # "是否将 Windows Search 替换为 PowerToys Run"
            FluentIcon.POWER_BUTTON,
            True,
        )
        self.vBoxLayout.addWidget(self.enableCard)
        # 添加 VersionCard
        self.vBoxLayout.addWidget(
            VersionCard(
                self.tr("Version Update"),  # "版本更新"
                self.tr("Current Version: {version}").format(
                    version=version
                ),  # "当前版本：{version}"
                self.tr("Check for Updates"),  # "检查更新"
                FluentIcon.UPDATE,
                on_check_update=self.parent().on_check_update_button_clicked,
            )
        )
        # 添加 AboutCard
        self.vBoxLayout.addWidget(
            AboutCard(
                self.tr("About"),  # "关于"
                "Copyright © 2025 Illustar0.",
                "Github",
                "https://github.com/Illustar0/PowerToysRunEnhance",
                FluentIcon.INFO,
            )
        )
