from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    isDarkTheme,
)

from src.core.interfaces import IMainWindow
from src.utils import get_base_path


class MainWindow(IMainWindow):
    enable_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setMinimumWidth(650)
        self.setWindowTitle("WindowsSearchUtility")
        self.setWindowIcon(QIcon(str(get_base_path() / "resources" / "logo.png")))

    def _onThemeChangedFinished(self):
        super()._onThemeChangedFinished()

        # 云母特效启用时需要增加重试机制
        if self.isMicaEffectEnabled():
            QTimer.singleShot(
                100,
                lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()),
            )

    def show_(self):
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event):
        # 忽略退出事件
        event.ignore()
        self.hide()
