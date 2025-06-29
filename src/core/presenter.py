from PySide6.QtCore import Signal, Slot
from loguru import logger

from src.core.interfaces import ITrayIconPresenter, ITrayIcon, IApplicationModel


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
