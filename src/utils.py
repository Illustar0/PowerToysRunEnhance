import ctypes
import sys
import winreg

import psutil
import win32api
import win32con
import win32process
from PySide6.QtCore import Qt
from loguru import logger

from src.core.interfaces import IAggressiveDialog


def get_process_path(hwnd) -> str:
    """获取窗口所属的进程名"""
    try:
        # 获取进程ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        # 打开进程
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False,
            pid,
        )
        # 获取进程名
        process_name = win32process.GetModuleFileNameEx(handle, 0)
        win32api.CloseHandle(handle)
        return process_name
    except:
        return ""


# So Microsoft, fuck you!
class AggressiveDialog(IAggressiveDialog):
    """用于抢占焦点的 QWidget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowOpacity(0)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.Tool
        )

    def get_focus(self):
        self.show()
        force_set_foreground_window(self.winId())


def force_set_foreground_window(hwnd: int):
    """使用 AttachThreadInput 来强制将窗口设为前台"""
    user32 = ctypes.windll.user32

    foreground_thread_id = user32.GetWindowThreadProcessId(
        user32.GetForegroundWindow(), None
    )
    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

    user32.AttachThreadInput(foreground_thread_id, current_thread_id, True)

    try:
        user32.BringWindowToTop(hwnd)
        user32.ShowWindow(hwnd, 5)
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)
    finally:
        user32.AttachThreadInput(foreground_thread_id, current_thread_id, False)


def get_app_current_theme():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        0,
        winreg.KEY_READ,
    ) as key:
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    if value == 1:
        return "light"
    else:
        return "dark"


def touch_run_at_startup():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_ALL_ACCESS,
    ) as key:
        try:
            value, _ = winreg.QueryValueEx(key, "WindowsSearchUtility")
            if value != sys.executable:
                winreg.SetValueEx(
                    key, "WindowsSearchUtility", 0, winreg.REG_SZ, sys.executable
                )
        except FileNotFoundError:
            winreg.SetValueEx(
                key, "WindowsSearchUtility", 0, winreg.REG_SZ, sys.executable
            )
        except Exception as e:
            logger.error(f"Error occurred when trying touch run at startup: {e}")


def get_run_at_startup() -> bool:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_READ,
    ) as key:
        try:
            value, _ = winreg.QueryValueEx(key, "WindowsSearchUtility")
            if value != sys.executable:
                return False
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error occurred when trying get run at startup: {e}")
            return False


def enable_run_at_startup():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_WRITE,
    ) as key:
        winreg.SetValueEx(key, "WindowsSearchUtility", 0, winreg.REG_SZ, sys.executable)


def disable_run_at_startup():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_WRITE,
    ) as key:
        try:
            winreg.DeleteValue(key, "WindowsSearchUtility")
        except FileNotFoundError:
            logger.error("Key not found.")
        except Exception as e:
            logger.error(f"Error occurred when trying disable run at startup: {e}")


def find_processes_by_name(target_names: list | set) -> bool:
    """
    查找进程
    """
    target_set = set(target_names)

    for process in psutil.process_iter(["name"]):
        try:
            process_name = process.info["name"]
            if process_name in target_set:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False
