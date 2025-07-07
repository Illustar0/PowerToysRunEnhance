from typing import Dict

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QSystemTrayIcon
from qfluentwidgets import (
    FluentWindow,
    FluentIcon,
    NavigationAvatarWidget,
    NavigationItemPosition,
    isDarkTheme,
)

from src.core.interfaces import IFluentWindow
from src.ui.interfaces.main import MainInterface
from src.ui.interfaces.setting import SettingInterface


class MainWindow(IFluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.interfaces: Dict[str, QWidget] = {}

        # 注册子界面
        self.interfaces["Main"] = MainInterface("Main", version="1.0")
        self.interfaces["Setting"] = SettingInterface("Setting")

        self.init_navigation()

    def init_navigation(self):
        self.addSubInterface(self.interfaces["Main"], FluentIcon.HOME, "Home")
        self.navigationInterface.addSeparator()
        self.navigationInterface.addWidget(
            routeKey="Avatar",
            widget=NavigationAvatarWidget("Illustar0", "./resources/Avatar.png"),
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self.interfaces["Setting"],
            FluentIcon.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM,
        )

    def _onThemeChangedFinished(self):
        super()._onThemeChangedFinished()

        # 云母特效启用时需要增加重试机制
        if self.isMicaEffectEnabled():
            QTimer.singleShot(
                100,
                lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()),
            )

    def on_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """
        处理托盘图标的激活事件
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def closeEvent(self, event):
        # 忽略退出事件
        event.ignore()
        self.hide()
