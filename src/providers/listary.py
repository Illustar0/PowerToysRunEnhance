import ctypes
import time
from typing import Optional

import pywinauto
import win32con
from PySide6.QtCore import Signal
from loguru import logger
from pydantic import BaseModel, Field
from pynput.keyboard import Controller, Key, KeyCode
from pywinauto import Application
from .base import IProvider, IProviderContext, ProviderMeta

__meta__ = ProviderMeta(
    provider_name="Listary",
    provider_process_name=["Listary.exe"],
    required_config="Listary",
)


class ListaryConfig(BaseModel):
    shortcut: str = Field("Ctrl-Ctrl", description="Listary 快捷键")
    """CommandPalette 快捷键"""
    input_speed_factor: float = Field(0.3, description="模拟输入速率因子")
    """模拟输入速率因子"""
    setting_delay: float = Field(0.1, description="稳定延迟")
    """稳定延迟"""


class Listary(IProvider):
    inputDone = Signal()
    SPECIAL_KEYS = {
        "alt": Key.alt,
        "ctrl": Key.ctrl,
        "shift": Key.shift,
        "space": Key.space,
        "win": Key.cmd,
    }

    def __init__(self, context: IProviderContext, /):
        super().__init__(context)
        self.context = context
        logger.debug(self.context.provider_config)

        # 缓存 hwnd
        self.current_hwnd: int | None = None
        self.provider_app: Application | None = None

    @property
    def config(self) -> ListaryConfig:
        return ListaryConfig.model_validate(self.context.provider_config)

    def _map_key(self, key: str) -> str:
        """将输入键映射到对应的键值"""
        return self.SPECIAL_KEYS.get(key.lower(), key.lower())

    def launch(self) -> bool:
        logger.info(f"Launching {self}")
        shortcut = self.config.shortcut
        keyboard = Controller()

        key_combinations = shortcut.split("-")
        for combination in key_combinations:
            if "+" in combination:
                keys = combination.split("+")
                mapped_keys = [self._map_key(key) for key in keys]
                with keyboard.pressed(*mapped_keys):
                    pass
            else:
                key = self._map_key(combination)
                keyboard.tap(key)
            time.sleep(0.05)
        return True

    def _connect_to_provider(self) -> Optional[pywinauto.WindowSpecification]:
        """连接到 Provider 窗口"""
        try:
            if (
                self.provider_app is None
                or self.current_hwnd != self.context.provider_hwnd
            ):
                logger.debug(
                    f"Connecting to provider with HWND: {self.context.provider_hwnd}"
                )
                self.provider_app = pywinauto.Application(backend="uia").connect(
                    handle=self.context.provider_hwnd
                )
                self.current_hwnd = self.context.provider_hwnd
            return self.provider_app
        except Exception as e:
            logger.error(f"Failed to connect to provider: {e}")
            # 重置
            self.provider_app = None
            self.current_hwnd = None
            return None

    def send_input(self):
        provider_app = self._connect_to_provider()
        try:
            # 傻逼 PyCharm ，瞎鸡巴提示 DeprecationWarning
            # noinspection PyDeprecation
            provider_window = provider_app.window(handle=self.current_hwnd)
            provider_window.wait("ready", timeout=3)
            query_box = provider_window.child_window(auto_id="PART_SearchBox")
            query_box.wait("ready", timeout=3)

            # 等待狗屎 Listary 初始化完成
            print(self.config.setting_delay)
            time.sleep(self.config.setting_delay)
        except Exception as e:
            logger.error(f"Waiting for Provider to be ready failed: {e}")
            self.inputDone.emit()
            return

        # 设置焦点。一般没有开启的必要
        if self.context.common_config.auto_focus:
            logger.info("Auto focus")
            try:
                if query_box.window_text() != "":
                    query_box.set_text("")
                query_box.set_focus()
            except Exception as e:
                logger.warning(f"Auto focus failed: {e}")
                pass

        try:
            keyboard = Controller()

            # 校准 CapsLock 键状态
            caps_lock_state = (
                ctypes.windll.user32.GetKeyState(win32con.VK_CAPITAL) & 0x0001
            )
            if caps_lock_state != 0:
                capslock = True
            else:
                capslock = False
            if self.context.user_input[0].capslock != capslock:
                keyboard.tap(KeyCode.from_vk(win32con.VK_CAPITAL))
            logger.info(self.config.input_speed_factor)
            # 重放，根据 input_speed_factor 加速
            while self.context.user_input:
                logger.debug(self.context.user_input)
                input_data = self.context.user_input.popleft()
                if input_data.msg in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN):
                    keyboard.press(KeyCode.from_vk(input_data.vkCode))
                else:
                    keyboard.release(KeyCode.from_vk(input_data.vkCode))

                # 如果还有下一个输入，计算延时
                if self.context.user_input:
                    next_input_data = self.context.user_input[0]
                    time_to_sleep = (
                        (next_input_data.time - input_data.time)
                        / 1000
                        * self.config.input_speed_factor
                    )
                    time.sleep(time_to_sleep)

            logger.debug(self.context.user_input)
        except Exception as e:
            logger.error(e)
        # 防止死锁
        finally:
            self.inputDone.emit()

    def cleanup(self) -> None:
        pass
