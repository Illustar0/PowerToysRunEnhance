import os

from PySide6.QtCore import Slot, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSystemTrayIcon, QApplication
from loguru import logger
from qfluentwidgets import Action, FluentIcon
from qfluentwidgets.common.icon import toQIcon
from qfluentwidgets.components.material import AcrylicSystemTrayMenu, AcrylicMenu

from src.core.interfaces import ITrayIcon


class TrayIcon(ITrayIcon):
    enable_changed = Signal(bool)
    request_reset_status = Signal()
    activated = Signal(QSystemTrayIcon.ActivationReason)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # 托盘图标
        self.tray_icon: QSystemTrayIcon

        # 托盘菜单
        self.menu: AcrylicSystemTrayMenu
        self.palette_menu: AcrylicMenu
        self.advanced_menu: AcrylicMenu

        # 托盘菜单的 Action
        self.enable_action: Action
        self.palette_menu_color_action: Action

        # 初始化托盘图标
        self._init_tray_icon()

    def _init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("resources/logo.png"))
        self.tray_icon.setToolTip(self.tr("WindowsSearchUtility"))
        self.tray_icon.activated.connect(self.activated.emit)
        logger.debug("Tray icon loaded")

        self.menu = AcrylicSystemTrayMenu()
        self.enable_action = Action(
            toQIcon(FluentIcon.ACCEPT),
            self.tr("Enable"),
            checkable=True,
            checked=True,
            ToolTip="Feature Flag",
        )
        self.enable_action.triggered.connect(
            lambda: self.enable_changed.emit(self.enable_action.isChecked())
        )

        self.advanced_menu_reset_status_action = Action(
            FluentIcon.SYNC,
            self.tr("Reset status"),
            triggered=lambda: self.request_reset_status.emit(),
        )

        self.advanced_menu = AcrylicMenu(self.tr("Advanced"), self.menu)
        self.advanced_menu.setIcon(FluentIcon.SETTING)
        self.advanced_menu.addAction(self.advanced_menu_reset_status_action)
        self.advanced_menu.addSeparator()
        self.advanced_menu.addAction(
            Action(
                FluentIcon.CODE,
                self.tr("Edit Config"),
                triggered=lambda: os.startfile("config.toml"),
            )
        )

        self.menu.addAction(self.enable_action)
        self.menu.addSeparator()
        self.menu.addMenu(self.advanced_menu)
        self.menu.addAction(
            Action(
                FluentIcon.POWER_BUTTON,
                self.tr("Quit"),
                triggered=QApplication.instance().quit,
            )
        )

        self.tray_icon.setContextMenu(self.menu)

        self.enable_changed.connect(self._change_enable_icon)

    def show(self):
        self.tray_icon.show()

    @Slot(bool)
    def set_enabled(self, enabled: bool):
        self.enable_action.setChecked(enabled)
        self._change_enable_icon(enabled)

    @Slot(bool)
    def _change_enable_icon(self, enabled: bool):
        if enabled:
            self.enable_action.setIcon(toQIcon(FluentIcon.ACCEPT))
        else:
            self.enable_action.setIcon(QIcon())

    def refresh_enable_icon(self):
        """强制刷新 Enable 的 Icon"""
        if self.enable_action.isChecked():
            self.enable_action.setIcon(toQIcon(FluentIcon.ACCEPT))
        else:
            self.enable_action.setIcon(QIcon())
