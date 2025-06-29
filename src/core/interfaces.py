from abc import ABC, abstractmethod, ABCMeta
from collections import deque
from typing import Protocol, Optional, Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentWindow

from src.core.models import CommonConfigModel, AppConfigModel
from src.core.models import InputData


class QWidgetABCMeta(type(QWidget), ABCMeta):
    pass


class QObjectABCMeta(type(QObject), ABCMeta):
    pass


class WindowABCMeta(type(FluentWindow), ABCMeta):
    pass


class IProviderContext(Protocol):
    """Provider 上下文接口"""

    provider_process_name: str
    provider_path: Optional[str]
    provider_hwnd: Optional[int]
    common_config: CommonConfigModel
    provider_config: Optional[dict]
    user_input: Optional[deque[InputData]]


class IProviderMeta(Protocol):
    """Provider 元数据接口"""

    provider_name: str
    provider_process_name: list[str]
    required_config: Optional[str]


class IProviderSettingGUI(QWidget, ABC, metaclass=QWidgetABCMeta):
    pass


class IProvider(QObject, ABC, metaclass=QObjectABCMeta):
    """Provider 接口"""

    inputDone = Signal()

    def __init__(self, context: IProviderContext, /):
        super().__init__()
        self.context = context

    @abstractmethod
    def launch(self) -> bool:
        """启动 Provider"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理 Provider资源"""
        pass

    @abstractmethod
    def send_input(self) -> None:
        """发送输入"""
        pass


class IProviderRegistry(ABC):
    """Provider 注册表接口"""

    @abstractmethod
    def register_provider(
        self,
        provider_name: str,
        provider_meta: IProviderMeta,
        provider_class: type[IProvider],
        provider_setting_gui_class: type[IProviderSettingGUI] | None = None,
    ) -> None:
        """注册 Provider"""
        pass

    @abstractmethod
    def get_provider_class(self, provider_name: str) -> Optional[type[IProvider]]:
        """获取 Provider 类"""
        pass

    @abstractmethod
    def get_provider_setting_gui_class(
        self, provider_name: str
    ) -> Optional[type[IProviderSettingGUI]]:
        """获取 Provider 设置 GUI 类"""
        pass

    @abstractmethod
    def get_provider_meta(self, provider_name: str) -> Optional[IProviderMeta]:
        """获取 Provider 元数据"""
        pass

    @abstractmethod
    def get_all_provider_names(self) -> list[str]:
        """获取所有 Provider名称"""
        pass


class IProviderFactory(QObject, ABC, metaclass=QObjectABCMeta):
    inputDone = Signal()

    @property
    @abstractmethod
    def provider_instances(self) -> dict[str, IProvider]:
        """返回实例字典。"""
        pass

    @abstractmethod
    def create_instance(
        self, provider_name: str, provider_context: IProviderContext | None = None
    ) -> IProvider:
        pass

    def get_instance(self, provider_name: str) -> IProvider | None:
        pass


class IProviderManager(QObject, ABC, metaclass=QObjectABCMeta):
    """Provider 管理器接口"""

    inputDone = Signal()

    @abstractmethod
    def provider_launch(
        self, provider_name: str, provider_context: IProviderContext
    ) -> bool:
        """启动 Provider"""
        pass

    @abstractmethod
    def provider_cleanup(self, provider_name: str) -> None:
        """清理 Provider"""
        pass

    @abstractmethod
    def provider_send_input(self, provider_name: str) -> None:
        """清理 Provider"""
        pass

    @abstractmethod
    def provider_run(self, provider_name: str, method: str):
        pass


class IKeyboardHook(QObject, ABC, metaclass=QObjectABCMeta):
    """KeyboardHook 接口"""

    @abstractmethod
    def start_listening(self) -> None:
        """开始监听"""
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """停止监听"""
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """设置启用状态"""
        pass

    @abstractmethod
    def on_windows_search_close(self):
        pass

    @abstractmethod
    def on_provider_start_failed(self):
        pass

    @abstractmethod
    def on_provider_started(self, provider_hwnd: int):
        pass


class IWindowHook(QObject, ABC, metaclass=QObjectABCMeta):
    """WindowHook 接口"""

    providerStarted = Signal()
    windowsSearchClosed = Signal()
    windowsSearchStarted = Signal()

    @abstractmethod
    def set_provider_process_names(self, process_names: list[str]) -> None:
        """设置 Provider 进程名"""
        pass

    @abstractmethod
    def set_hook(self) -> None:
        """设置钩子"""
        pass

    @abstractmethod
    def unset_hook(self) -> None:
        """清理钩子"""
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        pass


class IConfigurationService(QObject, ABC, metaclass=QObjectABCMeta):
    """配置服务接口"""

    configChanged = Signal()

    @property
    @abstractmethod
    def data(self) -> AppConfigModel:
        pass

    @data.setter
    @abstractmethod
    def data(self, value: AppConfigModel) -> None:
        pass

    @abstractmethod
    def save(self) -> None:
        """保存配置"""
        pass

    @abstractmethod
    def load(self) -> None:
        """加载配置"""
        pass


class ITrayIcon(QWidget, ABC, metaclass=QWidgetABCMeta):
    """主 Presenter 接口"""

    enable_changed = Signal(bool)
    request_reset_status = Signal()

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """切换启用状态"""
        pass

    @abstractmethod
    def show(self):
        pass


class ITrayIconPresenter(QObject, ABC, metaclass=QObjectABCMeta):
    """主 Presenter 接口"""

    reset_status = Signal()

    @abstractmethod
    def request_reset_status(self):
        pass


class IApplicationModel(QObject, ABC, metaclass=QObjectABCMeta):
    """应用模型接口"""

    enabled_changed = Signal(bool)
    active_provider_changed = Signal(str)

    @abstractmethod
    def is_enabled(self) -> bool:
        """是否启用"""
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """设置启用状态"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """获取版本"""
        pass

    @abstractmethod
    def get_active_provider(self) -> str:
        """获取活动 Provider"""
        pass

    @abstractmethod
    def set_active_provider(self, provider_name: str) -> str:
        """设置活动 Provider"""
        pass


class IEventBus(ABC):
    """事件总线接口"""

    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """订阅事件"""
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """取消订阅"""
        pass

    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件"""
        pass
