import ctypes.wintypes
import sys
from typing import Any

import win32con
from PySide6.QtCore import Signal, Slot, QObject, QAbstractNativeEventFilter
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QSystemTrayIcon
from loguru import logger
from qfluentwidgets import Theme, qconfig
from qframelesswindow.utils import getSystemAccentColor

from src.core.interfaces import (
    ITrayIconPresenter,
    ITrayIcon,
    IApplicationModel,
    IMainWindowPresenter,
    IMainWindow,
    ISettingInterface,
    IConfigurationService,
    ISettingInterfacePresenter,
    IMainInterface,
    IMainInterfacePresenter,
    IProviderRegistry,
)
from src.utils import (
    get_app_current_theme,
    enable_run_at_startup,
    disable_run_at_startup,
    get_run_at_startup,
)


class NativeEventFilter(QAbstractNativeEventFilter, QObject):
    """原生事件过滤"""

    themeChanged = Signal(Theme)
    themeColorChanged = Signal(QColor)

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
                if sys.platform in ["win32", "darwin"]:
                    if getSystemAccentColor().name() != qconfig.themeColor:
                        self.themeColorChanged.emit(getSystemAccentColor())
            return True
        return False


class TrayIconPresenter(ITrayIconPresenter):
    reset_status = Signal()

    def __init__(self, tray_icon: ITrayIcon, application_model: IApplicationModel):
        super().__init__()
        self.tray_icon = tray_icon
        self.app = application_model

        self.tray_icon.set_run_at_startup_enabled(get_run_at_startup())

        self.tray_icon.request_reset_status.connect(self.request_reset_status)
        self.tray_icon.run_at_startup_action_triggered.connect(
            self.on_run_at_startup_action_triggered
        )
        self.tray_icon.enable_changed.connect(self.app.set_enabled)

        self.app.enabled_changed.connect(self.tray_icon.set_enabled)

    @Slot()
    def request_reset_status(self):
        self.reset_status.emit()

    @Slot()
    def on_theme_changed(self):
        """强制刷新 Enable 图标"""
        self.tray_icon.refresh_enable_icon()

    def on_run_at_startup_action_triggered(self, enabled: bool):
        if enabled:
            enable_run_at_startup()
        else:
            disable_run_at_startup()


class MainWindowPresenter(IMainWindowPresenter):
    def __init__(self, main_window: IMainWindow, application_model: IApplicationModel):
        super().__init__()
        self.main_window = main_window
        self.app = application_model

    @Slot(str)
    def onMessageReceived(self, message: str):
        if message == "show":
            self.main_window.show_()

    @Slot(QSystemTrayIcon.ActivationReason)
    def onTrayIconActivated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.main_window.show_()


class MainInterfacePresenter(IMainInterfacePresenter):
    def __init__(
        self, main_interface: IMainInterface, application_model: IApplicationModel
    ):
        self.main_interface = main_interface
        self.app = application_model

        self.main_interface.enableChanged.connect(self.app.set_enabled)

        self.app.enabled_changed.connect(self.main_interface.setEnable)

        self.main_interface.setEnable(self.app.is_enabled())


class SettingInterfacePresenter(ISettingInterfacePresenter):
    def __init__(
        self,
        setting_interface: ISettingInterface,
        config_service: IConfigurationService,
        provider_registry: IProviderRegistry,
    ):
        super().__init__()
        self.setting_interface = setting_interface
        self.config_service = config_service
        self.provider_registry = provider_registry
        self.settingCardDict = {}
        for SettingCardGroup in self.setting_interface.listSettingCardGroups():
            for SettingCard in SettingCardGroup.listSettingCard():
                self.settingCardDict.update({SettingCard.configPath: SettingCard})

                if SettingCard.configPath == "Common.active_provider":
                    SettingCard.addItems(self.provider_registry.get_provider_names())
                SettingCard.setValue(self.config_service.get(SettingCard.configPath))
                SettingCard.valueChanged.connect(self._onSettingCardValueChanged)

    def _onSettingCardValueChanged(self, config_path: str, value: Any):
        if config_path == "Common.active_provider":
            self.config_service.set(
                config_path, self.provider_registry.get_provider_names()[value]
            )
            return
        self.config_service.set(config_path, value)

    @Slot()
    def onConfigChanged(self, path: str):
        if path in self.settingCardDict:
            self.settingCardDict[path].setValue(self.config_service.get(path))
        elif path == "All":
            for SettingCardGroup in self.setting_interface.listSettingCardGroups():
                for SettingCard in SettingCardGroup.listSettingCard():
                    SettingCard.setValue(
                        self.config_service.get(SettingCard.configPath)
                    )
