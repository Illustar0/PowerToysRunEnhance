import os
from collections import deque
from enum import Enum, auto
from os import PathLike
from typing import Dict, List, Optional, Any, Final

import tomlkit
from PySide6.QtCore import Signal, QFileSystemWatcher
from loguru import logger

from src.core.interfaces import (
    IApplicationModel,
    IConfigurationService,
    IEventBus,
)
from src.core.models import CommonConfigModel, AppConfigModel
from src.core.models import InputData

__VERSION__ = "0.1.0"
DEFAULT_CONFIG: Final[dict] = {
    "Common": {
        "auto_focus": True,
        "active_provider": "Command Palette",
        "language": "en_US",
    },
    "Providers": {
        "PowerToysRun": {"shortcut": "Alt+Space", "input_speed_factor": 0.3},
        "CommandPalette": {"shortcut": "Win+Alt+Space", "input_speed_factor": 0.3},
        "Listary": {
            "shortcut": "Ctrl-Ctrl",
            "input_speed_factor": 0.3,
            "setting_delay": 0.1,
        },
    },
}


class ProviderStatus(Enum):
    """Provider状态枚举"""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class WindowsSearchStatus(Enum):
    """Windows搜索状态枚举"""

    CLOSED = auto()
    VISIBLE = auto()
    INVISIBLE = auto()


class ProviderContext:
    """Provider上下文实现"""

    provider_process_name: str = ""
    provider_path: Optional[str] = None
    provider_hwnd: Optional[int] = None
    common_config: CommonConfigModel
    provider_config: Optional[dict] = None
    user_input: Optional[deque[InputData]]


class ApplicationModel(IApplicationModel):
    """应用模型 - 管理应用状态和数据"""

    # 信号定义
    enabled_changed = Signal(bool)
    active_provider_changed = Signal(str)

    def __init__(self, config_service: IConfigurationService, parent=None):
        super().__init__(parent)
        self._config_service = config_service
        self._logger = logger
        self._enabled = True
        self._active_provider = config_service.data.Common.active_provider
        self._version = __VERSION__

    def is_enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """设置启用状态"""
        if self._enabled != enabled:
            self._enabled = enabled
            self.enabled_changed.emit(enabled)
            self._logger.info(
                f"The application enabled status has been changed to: {enabled}"
            )

    def get_version(self) -> str:
        """获取版本"""
        return self._version

    def get_active_provider(self) -> str:
        """获取活动provider"""
        return self._active_provider

    def set_active_provider(self, provider_name: str) -> None:
        """设置活动provider"""
        if self._active_provider != provider_name:
            self._active_provider = provider_name
            self.active_provider_changed.emit(provider_name)
            self._logger.info(f"Active Provider has been changed to: {provider_name}")


class ConfigurationService(IConfigurationService):
    configChanged = Signal()

    def __init__(self, config_path: str | PathLike = "./config.toml"):
        super().__init__()
        self.config_path = config_path
        self._data: AppConfigModel | None = None

        if os.path.exists(self.config_path):
            self.load()
        else:
            self._data = AppConfigModel.model_validate(DEFAULT_CONFIG)
            logger.info(f"Configuration loaded from default config")
            self.save()

        # 自动重载
        self._watcher = QFileSystemWatcher()
        self._watcher.addPath(self.config_path)
        self._watcher.fileChanged.connect(self.load)

    @property
    def data(self) -> AppConfigModel:
        return self._data

    @data.setter
    def data(self, value: AppConfigModel) -> None:
        if self._data != value:
            # 使用 Pydantic 的 model_validate 来验证新值
            validated_value = AppConfigModel.model_validate(value.model_dump())
            self._data = validated_value
            self.save()
            self.configChanged.emit()

    def load(self) -> None:
        """加载配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                toml_data = tomlkit.loads(f.read())
            # 💩
            # noinspection PyTypeChecker
            toml_data = dict(toml_data)
            self._data = AppConfigModel.model_validate(toml_data)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def save(self) -> None:
        """保存配置"""
        try:
            with open(self.config_path + ".wsu_temp", "w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(self._data.model_dump()))
            os.replace(self.config_path + ".wsu_temp", self.config_path)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")


class EventBus(IEventBus):
    """事件总线实现 - 遵循接口隔离原则"""

    def __init__(self):
        self._logger = logger
        self._subscribers: Dict[str, List[callable]] = {}

    def subscribe(self, event_type: str, handler: callable) -> None:
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._logger.debug(f"订阅事件: {event_type}")

    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """取消订阅"""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            self._logger.debug(f"取消订阅事件: {event_type}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件"""
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self._logger.error(f"事件处理器执行失败: {str(e)}")
            self._logger.debug(f"发布事件: {event_type}")
