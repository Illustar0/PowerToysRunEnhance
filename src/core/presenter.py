import ctypes.wintypes

import win32con
from PySide6.QtCore import Signal, Slot, QObject, QAbstractNativeEventFilter
from loguru import logger
from qfluentwidgets import Theme, qconfig

from src.core.interfaces import (
    ITrayIconPresenter,
    ITrayIcon,
    IApplicationModel,
    IMainWindowPresenter,
    IMainWindow,
)
from src.utils import get_app_current_theme


class NativeEventFilter(QAbstractNativeEventFilter, QObject):
    """原生事件过滤"""

    themeChanged = Signal(Theme)

    def __init__(self):
        QObject.__init__(self)
        QAbstractNativeEventFilter.__init__(self)

    def nativeEventFilter(self, event_type, message):
        msg = ctypes.wintypes.MSG.from_address(message.__int__())
        if msg.message == win32con.WM_SETTINGCHANGE:
            setting = ctypes.c_wchar_p(msg.lParam).value
            if setting == "ImmersiveColorSet":
                system_app_current_theme = (
                    Theme.LIGHT if get_app_current_theme() == "light" else Theme.DARK
                )
                if system_app_current_theme != qconfig.theme:
                    logger.debug(
                        f"System theme has changed, switch Qt theme to {system_app_current_theme}"
                    )
                    self.themeChanged.emit(system_app_current_theme)
                    return True
            return True
        return False


class TrayIconPresenter(ITrayIconPresenter):
    reset_status = Signal()

    def __init__(self, tray_icon: ITrayIcon, application_model: IApplicationModel):
        super().__init__()
        self.tray_icon = tray_icon
        self.app = application_model

        self.tray_icon.request_reset_status.connect(self.request_reset_status)
        self.tray_icon.enable_changed.connect(self.app.set_enabled)

        self.app.enabled_changed.connect(self.tray_icon.set_enabled)

    @Slot()
    def request_reset_status(self):
        self.reset_status.emit()

    @Slot()
    def on_theme_changed(self):
        """强制刷新 Enable 图标"""
        self.tray_icon.refresh_enable_icon()


class MainWindowPresenter(IMainWindowPresenter):
    reset_status = Signal()

    def __init__(self, main_window: IMainWindow, application_model: IApplicationModel):
        super().__init__()
        self.main_window = main_window
        self.app = application_model

        self.main_window.enable_changed.connect(self.app.set_enabled)

        self.app.enabled_changed.connect(self.main_window.set_enabled)

    @Slot(str)
    def on_message_received(self, message: str):
        if message == "show":
            self.main_window.show()
