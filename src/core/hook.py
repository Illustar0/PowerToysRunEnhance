import ctypes
from collections import deque
from ctypes import wintypes
from pathlib import Path
from typing import Final

import win32con
from PySide6.QtCore import Slot, Signal, QTimer
from loguru import logger
from pynput import keyboard

from src.core.interfaces import (
    IKeyboardHook,
    IWindowHook,
    IProviderContext,
    IProviderManager,
    IProviderRegistry,
    IConfigurationService,
)
from src.core.model import ProviderStatus, WindowsSearchStatus
from src.core.models import InputData
from src.utils import get_process_path

WINDOWS_SEARCH_PROCESS_NAME: Final[list[str]] = [
    "SearchHost.exe",
    "SearchUI.exe",
    "SearchAPP.exe",
]


class WindowHookWorker(IWindowHook):
    windowsSearchClosed = Signal()
    windowsSearchStarted = Signal(int)
    providerStarted = Signal(int)

    def __init__(
        self,
        provider_manager: IProviderManager,
        provider_registry: IProviderRegistry,
    ):
        super().__init__()
        self.callback: type[ctypes._FuncPointer] | None = None
        self.enable = True
        self.hook = None
        self.thread_id: int | None = None
        self.provider_manager: IProviderManager = provider_manager
        self.provider_registry: IProviderRegistry = provider_registry
        self.provider_process_name: list[str] | None = None
        self.previous_foreground_window_name: str | None = None

    @Slot(bool)
    def set_enabled(self, enabled: bool):
        self.enable = enabled

    @Slot()
    def touch_enable(self):
        self.enable = not self.enable

    @Slot(str)
    def set_provider_process_names_by_provider_name(self, process_name: str):
        self.provider_process_name = self.provider_registry.get_provider_meta(
            process_name
        ).provider_process_name

    # 定义回调函数
    # noinspection PyUnusedLocal
    def win_event_callback(
        self,
        hWinEventHook,
        event,
        hwnd,
        idObject,
        idChild,
        dwEventThread,
        dwmsEventTime,
    ):
        # 只有在启用状态下才处理事件
        if not self.enable:
            return

        if event == win32con.EVENT_SYSTEM_FOREGROUND:
            process_path = Path(get_process_path(hwnd))
            process_name = process_path.name
            logger.debug(f"Foreground Window: {hwnd}:{process_name}")
            if self.previous_foreground_window_name in WINDOWS_SEARCH_PROCESS_NAME:
                self.windowsSearchClosed.emit()

            elif process_name in WINDOWS_SEARCH_PROCESS_NAME:
                self.windowsSearchStarted.emit(hwnd)
                pass
            elif process_name in self.provider_process_name:
                self.providerStarted.emit(hwnd)
                pass

            self.previous_foreground_window_name = process_name

    # 注册 Hook
    def set_hook(self):
        # 如果线程启动时处于禁用状态，则直接返回
        if not self.enable:
            return

        WinEventProcType = ctypes.WINFUNCTYPE(
            None,
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.HWND,
            wintypes.LONG,
            wintypes.LONG,
            wintypes.DWORD,
            wintypes.DWORD,
        )

        self.callback = WinEventProcType(self.win_event_callback)
        user32 = ctypes.windll.user32

        # 前台窗口改变
        self.hook = user32.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,
            win32con.EVENT_SYSTEM_FOREGROUND,
            0,
            self.callback,
            0,
            0,
            win32con.WINEVENT_OUTOFCONTEXT,
        )

        logger.info("Window hook is set")

    @Slot()
    def unset_hook(self):
        if self.hook:
            # 取消 Hook
            logger.info("The hook is unset")
            user32 = ctypes.windll.user32
            user32.UnhookWinEvent(self.hook)
            self.hook = None

    def run(self):
        """线程将要执行的主函数"""
        self.set_hook()

    def shutdown(self):
        user32 = ctypes.windll.user32
        if self.thread_id:
            logger.info(f"Posting WM_QUIT to thread ID: {self.thread_id}")
            # 关键点3: 使用PostThreadMessageW发送WM_QUIT消息
            user32.PostThreadMessageW(self.thread_id, win32con.WM_QUIT, 0, 0)
            self.thread_id = None
        else:
            logger.warning(
                "Shutdown called but thread ID is not set. Maybe the loop never started?"
            )


class KeyboardHookWorker(IKeyboardHook):
    launchProvider = Signal(str, IProviderContext)

    def __init__(
        self,
        app_config: IConfigurationService,
        provider_registry: IProviderRegistry,
        provider_manager: IProviderManager,
        provider_context: IProviderContext,
    ):
        super().__init__()
        self.enable = True
        self.listening = False
        self.app_config = app_config
        self.provider_manager = provider_manager
        self.provider_registry: IProviderRegistry = provider_registry
        self.provider_context: IProviderContext = provider_context
        self.windows_search_hwnd = None

        self.windows_search_status: WindowsSearchStatus = WindowsSearchStatus.INVISIBLE

        self.provider_status: ProviderStatus = ProviderStatus.COMPLETED
        self.provider_process_name = None
        self.listener = keyboard.Listener(win32_event_filter=self.win32_event_filter)
        self.listener.start()

    def set_provider_process_name(self, process_name):
        self.provider_process_name = process_name

    def win32_event_filter(self, msg, data):
        if not self.enable or not self.listening:
            return
        logger.debug(f"pynput 捕获到按键 {data.vkCode},flags={data.flags},msg={msg}")
        if (
            data.vkCode
            not in (
                win32con.VK_LMENU,
                win32con.VK_RMENU,
                win32con.VK_LWIN,
                win32con.VK_LWIN,
            )
            and msg
            in (
                win32con.WM_KEYUP,
                win32con.WM_KEYDOWN,
                win32con.WM_SYSKEYDOWN,
                win32con.WM_SYSKEYUP,
            )
            and (data.flags & win32con.LLKHF_INJECTED) == 0
        ):
            """
            data.flags & win32con.LLKHF_INJECTED == 0 表示 LLKHF_INJECTED ，意味着这个输入是模拟键盘事件
            """

            # 防止意外拉起 Provider
            if (
                self.provider_status == ProviderStatus.COMPLETED
                and self.windows_search_status == WindowsSearchStatus.CLOSED
            ):
                self.stop_listening()
                return

            # 构建 ProviderContext

            if self.provider_status is ProviderStatus.COMPLETED:
                logger.debug("尝试构建")
                self.provider_context.common_config = self.app_config.data.Common
                self.provider_context.provider_config = (
                    self.app_config.data.Providers.get(
                        self.provider_registry.get_provider_meta(
                            self.app_config.data.Common.active_provider
                        ).required_config
                    )
                )
                logger.info(self.app_config.data.Providers)
                logger.info(
                    self.app_config.data.Providers.get(
                        self.provider_registry.get_provider_meta(
                            self.app_config.data.Common.active_provider
                        ).required_config
                    )
                )
                self.provider_context.user_input = deque()

            # 检查 CapsLock 按键情况
            caps_lock_state = (
                ctypes.windll.user32.GetKeyState(win32con.VK_CAPITAL) & 0x0001
            )
            if caps_lock_state != 0:
                capslock = True
            else:
                capslock = False

            # noinspection PyUnboundLocalVariable
            # 捕获输入

            self.provider_context.user_input.append(
                InputData(
                    msg=msg,
                    vkCode=data.vkCode,
                    flags=data.flags,
                    time=data.time,
                    capslock=capslock,
                )
            )
            logger.debug(f"add {data.vkCode} {msg}")
            logger.info(self.provider_context.user_input)

            if self.provider_status is ProviderStatus.COMPLETED:
                self.provider_status = ProviderStatus.PENDING
                self.windows_search_status = WindowsSearchStatus.VISIBLE

                # 关闭开始菜单
                user32 = ctypes.windll.user32
                user32.PostMessageW(self.windows_search_hwnd, 0x0010, 0, 0)

                # 防止开始菜单抽风导致死锁
                QTimer.singleShot(500, self.on_windows_search_close)

            logger.debug(f"按键{data.vkCode}被阻止,flags={data.flags},msg={msg}")
            self.listener.suppress_event()

    @Slot()
    def set_enabled(self, enable: bool):
        self.enable = enable

    @Slot()
    def on_windows_search_close(self):
        if self.provider_status != ProviderStatus.PENDING:
            return
        self.windows_search_status = WindowsSearchStatus.INVISIBLE

        # 防止 Provider 启动失败导致死锁
        QTimer.singleShot(1000, self.on_provider_start_failed)
        self.provider_manager.provider_launch(
            self.app_config.data.Common.active_provider, self.provider_context
        )
        """self.launchProvider.emit(
            self.app_config.data.Common.active_provider, self.provider_context
        )"""

    def on_provider_start_failed(self):
        if self.provider_status == ProviderStatus.PENDING:
            self.provider_status = ProviderStatus.FAILED
            logger.error(f"Provider launch failed")
            self.stop_listening()

    @Slot(int)
    def on_provider_started(self, provider_hwnd: int):
        logger.debug("Provider started.")
        if self.provider_status != ProviderStatus.PENDING:
            return
        self.provider_status = ProviderStatus.RUNNING
        self.provider_context.provider_hwnd = provider_hwnd
        self.provider_manager.provider_send_input(
            self.app_config.data.Common.active_provider
        )

    @Slot(int)
    def start_listening(self, hwnd):
        self.listening = True
        self.windows_search_hwnd = hwnd

    @Slot()
    def stop_listening(self):
        logger.debug("Stop listening")
        self.listening = False
        self.provider_status = ProviderStatus.COMPLETED
        # del self.provider_context
        # self.provider_manager.cleanup_provider(self.app_config.data.Common.active_provider)
