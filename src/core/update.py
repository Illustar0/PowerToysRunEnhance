import httpx
from PySide6.QtCore import QThread, Signal, QObject, Slot
from PySide6.QtGui import QDesktopServices
from loguru import logger
from windows_toasts import (
    Toast,
    ToastButton,
    InteractableWindowsToaster,
    ToastActivatedEventArgs,
)

from src.core.constants import APP_ID, APP_NAME, GITHUB_REPO


class UpdateCheckWorker(QThread):
    updateResult = Signal(dict)
    updateError = Signal(str)

    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version

    def run(self):
        try:
            response = httpx.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            )
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")

            result = {
                "latest_version": latest_version,
                "current_version": self.current_version,
                "has_update": latest_version != self.current_version,
                "download_url": release_data.get("html_url", ""),
            }
            self.updateResult.emit(result)

        except Exception as e:
            self.updateError.emit(str(e))


class VersionUpdateService(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def check_update(self, current_version: str):
        self.update_worker = UpdateCheckWorker(current_version)
        self.update_worker.updateResult.connect(self._onUpdateCheckFinished)
        self.update_worker.updateError.connect(self._onUpdateCheckError)
        self.update_worker.start()

    @Slot(dict)
    def _onUpdateCheckFinished(self, result: dict):
        if result["has_update"]:
            interactableToaster = InteractableWindowsToaster(APP_NAME, APP_ID)
            newToast = Toast([f"v{result['latest_version']}", "Update available."])

            newToast.AddAction(ToastButton("Update now", "response=update"))
            newToast.AddAction(ToastButton("Not now", "response=no"))

            def activated_callback(activatedEventArgs: ToastActivatedEventArgs):
                if activatedEventArgs.arguments == "response=update":
                    QDesktopServices.openUrl(result["download_url"])
                else:
                    interactableToaster.remove_toast(newToast)

            newToast.on_activated = activated_callback

            interactableToaster.show_toast(newToast)

    @Slot(str)
    def _onUpdateCheckError(self, error: str):
        logger.error(error)
