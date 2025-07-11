import os
from collections import deque
from enum import Enum, auto
from os import PathLike
from typing import Dict, List, Optional, Any, Final

import tomlkit
from PySide6.QtCore import Signal, QFileSystemWatcher
from loguru import logger
from pydantic import BaseModel, create_model

from src.core.interfaces import (
    IApplicationModel,
    IConfigurationService,
    IEventBus,
    IProviderRegistry,
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
    """Provider execution status enumeration.

    This enum defines the possible states of a provider during its lifecycle.

    :ivar PENDING: Provider is waiting to be executed
    :ivar RUNNING: Provider is currently being executed
    :ivar COMPLETED: Provider has completed execution successfully
    :ivar FAILED: Provider execution has failed
    """

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


class WindowsSearchStatus(Enum):
    """Windows Search status enumeration.

    This enum defines the possible states of the Windows Search interface.

    :ivar CLOSED: Windows Search is closed
    :ivar VISIBLE: Windows Search is visible on screen
    :ivar INVISIBLE: Windows Search is present but not visible
    """

    CLOSED = auto()
    VISIBLE = auto()
    INVISIBLE = auto()


class ProviderContext:
    """Provider context implementation.

    This class holds the runtime context information for a provider,
    including process details, configuration, and user input data.

    :ivar provider_process_name: Name of the provider process
    :vartype provider_process_name: str
    :ivar provider_path: Path to the provider executable
    :vartype provider_path: Optional[str]
    :ivar provider_hwnd: Window handle of the provider
    :vartype provider_hwnd: Optional[int]
    :ivar common_config: Common configuration settings
    :vartype common_config: CommonConfigModel
    :ivar provider_config: Provider-specific configuration
    :vartype provider_config: Optional[dict]
    :ivar user_input: Queue of user input data
    :vartype user_input: Optional[deque[InputData]]
    """

    provider_process_name: str = ""
    provider_path: Optional[str] = None
    provider_hwnd: Optional[int] = None
    common_config: CommonConfigModel
    provider_config: Optional[dict] = None
    user_input: Optional[deque[InputData]]


class ApplicationModel(IApplicationModel):
    """Application model for managing application state and data.

    This class manages the core application state including enabled status,
    active provider configuration, and version information. It emits signals
    when important state changes occur.

    :param config_service: Configuration service instance
    :type config_service: IConfigurationService
    :param parent: Qt parent object
    :type parent: Optional[QObject]

    :signal enabled_changed: Emitted when application enabled status changes
    :signal active_provider_changed: Emitted when active provider changes
    """

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
        """Check if the application is currently enabled.

        :return: True if application is enabled, False otherwise
        :rtype: bool
        """
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Set the application enabled status.

        :param enabled: New enabled status
        :type enabled: bool

        :emits enabled_changed: When the enabled status changes
        """
        if self._enabled != enabled:
            self._enabled = enabled
            self.enabled_changed.emit(enabled)
            self._logger.info(
                f"The application enabled status has been changed to: {enabled}"
            )

    def get_version(self) -> str:
        """Get the application version.

        :return: Application version string
        :rtype: str
        """
        return self._version

    def get_active_provider(self) -> str:
        return self._config_service.data.Common.active_provider

    def set_active_provider(self, provider_name: str) -> None:
        current = self._config_service.data.Common.active_provider
        if current != provider_name:
            self._config_service.data.Common.active_provider = provider_name
            self.active_provider_changed.emit(provider_name)


class ConfigurationService(IConfigurationService):
    """Configuration service for managing application settings.

    This service handles loading, saving, and managing application configuration
    data. It supports automatic reloading when configuration files change and
    provides dot-notation access to nested configuration values.

    :param config_path: Path to the configuration file
    :type config_path: str | PathLike

    :signal configChanged: Emitted when configuration data changes
    """

    configChanged = Signal()

    def __init__(
        self,
        config_path: str | PathLike = "./config.toml",
        provider_registry: IProviderRegistry | None = None,
    ):
        super().__init__()
        self.config_path = config_path
        self._data: AppConfigModel | None = None
        if provider_registry is not None:
            self.model = self.create_app_config_from_registry(provider_registry)
        else:
            self.model = AppConfigModel
        if os.path.exists(self.config_path):
            self.load()
        else:
            self._data = self.model.model_validate(DEFAULT_CONFIG)
            logger.info(f"Configuration loaded from default config")
            self.save()

        # 自动重载
        self._watcher = QFileSystemWatcher()
        self._watcher.addPath(self.config_path)
        self._watcher.fileChanged.connect(self.load)

    def create_app_config_from_registry(
        self, provider_registry: IProviderRegistry
    ) -> type[BaseModel]:
        # 获取所有Provider的配置模型
        provider_configs = {}
        for _, meta in provider_registry.get_provider_metas().items():
            if meta.config_model:
                provider_configs[meta.required_config] = meta.config_model

        # 创建Providers模型
        ProvidersModel = create_model(
            "ProvidersModel",
            **{
                name: (config_class, config_class())
                for name, config_class in provider_configs.items()
            },
        )

        # 创建完整的AppConfigModel
        return create_model(
            "DynamicAppConfigModel",
            Common=(CommonConfigModel, CommonConfigModel()),
            Providers=(ProvidersModel, ProvidersModel()),
        )

    @property
    def data(self):
        """Get the current configuration data.

        :return: Current configuration data model
        :rtype: AppConfigModel
        """
        return self._data

    @data.setter
    def data(self, value) -> None:
        """Set the configuration data.

        :param value: New configuration data model
        :type value: AppConfigModel

        :emits configChanged: When configuration data changes
        """
        if self._data != value:
            # 使用 Pydantic 的 model_validate 来验证新值
            validated_value = self.model.model_validate(value.model_dump())
            self._data = validated_value
            self.save()
            self.configChanged.emit()

    def load(self) -> None:
        """Load configuration from file.

        Reads the configuration file and parses it into the data model.
        If loading fails, an error is logged but the operation continues.
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                toml_data = tomlkit.loads(f.read())
            # 💩
            # noinspection PyTypeChecker
            toml_data = dict(toml_data)
            self._data = self.model.model_validate(toml_data)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def save(self) -> None:
        """Save configuration to file.

        Writes the current configuration data to the file using atomic
        write operations to prevent data corruption.
        """
        try:
            with open(self.config_path + ".wsu_temp", "w", encoding="utf-8") as f:
                f.write(tomlkit.dumps(self._data.model_dump()))
            os.replace(self.config_path + ".wsu_temp", self.config_path)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, path: str) -> Any:
        """Get configuration value using dot notation path.

        :param path: Dot-separated path to the configuration value
        :type path: str

        :return: Configuration value at the specified path
        :rtype: Any

        :raises KeyError: If the configuration path does not exist

        """
        keys = path.split(".")
        current = self._data
        for key in keys:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise KeyError(f"Configuration path '{path}' not found")

        return current

    def set(self, path: str, value: Any) -> None:
        """Set the configuration value using dot notation path.

        :param path: Dot-separated path to the configuration value
        :type path: str
        :param value: Value to set at the specified path
        :type value: Any

        :raises KeyError: If the configuration path does not exist

        :emits configChanged: When configuration value is successfully set
        """
        keys = path.split(".")
        current = self._data

        # 导航到目标对象的父级
        for key in keys[:-1]:
            if hasattr(current, key):
                current = getattr(current, key)
            else:
                raise KeyError(f"Configuration path '{path}' not found")

        # 设置最终值
        final_key = keys[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
            # 触发配置变更事件
            self.save()
            self.configChanged.emit()
            logger.info(f"Configuration '{path}' set to '{value}'")
        else:
            raise KeyError(f"Configuration path '{path}' not found")


class EventBus(IEventBus):
    """Event bus implementation following the Interface Segregation Principle.

    This class provides a centralized event publishing and subscription system
    that allows different components to communicate without tight coupling.
    Events are identified by string types and can carry arbitrary data.

    :raises Exception: Logged when event handlers fail during execution
    """

    def __init__(self):
        self._logger = logger
        self._subscribers: Dict[str, List[callable]] = {}

    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to an event type.

        :param event_type: Type of event to subscribe to
        :type event_type: str
        :param handler: Callable to handle the event
        :type handler: callable
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        self._logger.debug(f"订阅事件: {event_type}")

    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from an event type.

        :param event_type: Type of event to unsubscribe from
        :type event_type: str
        :param handler: Handler to remove from subscriptions
        :type handler: callable
        """
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            self._logger.debug(f"取消订阅事件: {event_type}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribers.

        :param event_type: Type of event to publish
        :type event_type: str
        :param data: Optional data to send with the event
        :type data: Any

        :note: Failed handler executions are logged but do not stop other handlers
        """
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self._logger.error(f"事件处理器执行失败: {str(e)}")
            self._logger.debug(f"发布事件: {event_type}")
