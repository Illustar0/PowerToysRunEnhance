from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon
from qfluentwidgets import (
    FluentIcon,
    NavigationAvatarWidget,
    NavigationItemPosition,
    isDarkTheme,
)

from src.core.interfaces import IMainWindow
from src.ui.interfaces.main import MainInterface
from src.utils import get_base_path


class MainWindow(IMainWindow):
    enable_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("WindowsSearchUtility")
        self.setWindowIcon(QIcon(str(get_base_path() / "resources" / "logo.png")))

        # 注册子界面
        self.main_interface = MainInterface("Main", version="1.0")
        self.main_interface.enable_changed.connect(self.enable_changed.emit)

        self.setting_interface = MainInterface("Main", version="1.0")

        self.init_navigation()

    def init_navigation(self):
        self.addSubInterface(self.main_interface, FluentIcon.HOME, "Home")
        self.navigationInterface.addSeparator()
        self.navigationInterface.addWidget(
            routeKey="Avatar",
            widget=NavigationAvatarWidget(
                "Illustar0", str(get_base_path() / "resources" / "Avatar.png")
            ),
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(
            self.setting_interface,
            FluentIcon.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM,
        )

    def set_enabled(self, enabled: bool):
        self.main_interface.enableCard.set_enabled(enabled)

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
            self.show()

    def show(self):
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event):
        # 忽略退出事件
        event.ignore()
        self.hide()
