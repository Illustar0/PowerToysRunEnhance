from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    FluentIcon,
    SingleDirectionScrollArea,
)

from src.core.interfaces import ISettingInterface
from src.ui.interfaces.component import (
    SettingCardGroup,
    SwitchCard,
    ComboBoxCard,
)


class SettingInterface(ISettingInterface):
    def __init__(
        self,
        title: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", "-"))

        # 主布局
        self._vBoxLayout = QVBoxLayout(self)
        self._vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.view = QWidget()

        self.scrollArea = SingleDirectionScrollArea(orient=Qt.Orientation.Vertical)
        self.scrollArea.setWidget(self.view)
        self.scrollArea.enableTransparentBackground()

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._vBoxLayout.addWidget(self.scrollArea)

        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 20)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._settingCardGroups = []

    def init_ui(
        self, provider_setting_card_groups_dict: dict[str, type[SettingCardGroup]]
    ):
        # Common Settings Group
        commonGroup = SettingCardGroup(self.tr("Common"), self)

        autoFocusCard = SwitchCard(
            FluentIcon.PIN,
            self.tr("Auto focus"),
            self.tr(
                "Automatically focuses the Provider window."
            ),
            "Common.auto_focus",
            commonGroup,
        )

        activeProviderCard = ComboBoxCard(
            FluentIcon.APPLICATION,
            self.tr("Active provider"),
            self.tr("The currently active search provider"),
            "Common.active_provider",
            commonGroup,
        )

        languageCard = ComboBoxCard(
            FluentIcon.LANGUAGE,
            self.tr("Language"),
            self.tr("Application display language"),
            "Common.language",
            commonGroup,
        )

        commonGroup.addSettingCards([autoFocusCard, activeProviderCard])
        # commonGroup.addSettingCards([autoFocusCard, activeProviderCard, languageCard])
        self._settingCardGroups.append(commonGroup)

        # Add provider setting card groups
        for (
            provider_name_tr,
            provider_group,
        ) in provider_setting_card_groups_dict.items():
            if provider_group is not None:
                self._settingCardGroups.append(provider_group(provider_name_tr))

        # Add all groups to layout
        for group in self._settingCardGroups:
            self.vBoxLayout.addWidget(group)

        # 添加弹簧，顶端对其
        self.vBoxLayout.addStretch(1)

        self.view.setMinimumWidth(300)

    def listSettingCardGroups(self):
        return self._settingCardGroups
