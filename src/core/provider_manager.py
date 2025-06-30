import importlib
import inspect
import sys
from pathlib import Path
from typing import List, Optional, Dict, Type

from PySide6.QtCore import (
    Signal,
    QRunnable,
    QThreadPool,
    QMutex,
    QMutexLocker,
)
from loguru import logger
from src.core.interfaces import (
    IProvider,
    IProviderSettingGUI,
    IProviderRegistry,
    IProviderMeta,
    IProviderFactory,
    IProviderContext,
    IProviderManager,
)
from src.core.models import ProviderMeta


class ProviderWorker(QRunnable):
    def __init__(self, provider_instance, method, *args, **kwargs):
        super().__init__()
        self.provider_instance = provider_instance
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def run(self):
        getattr(self.provider_instance, self.method)(*self.args, **self.kwargs)


class ProviderRegistry(IProviderRegistry):
    def __init__(self):
        self.providers: Dict[str, Type[IProvider]] = {}
        self.provider_metas: Dict[str, IProviderMeta] = {}
        self.providers_guis: Dict[str, Type[IProviderSettingGUI]] = {}
        self._load_providers()

    def register_provider(
        self,
        provider_name: str,
        provider_meta: IProviderMeta,
        provider_class: type[IProvider],
        provider_setting_gui_class: type[IProviderSettingGUI] | None = None,
    ) -> None:
        self.providers[provider_name] = provider_class
        self.provider_metas[provider_name] = provider_meta
        self.providers_guis[provider_name] = provider_setting_gui_class

    def _load_providers(self):
        """加载 current_provider / 所有 provider"""
        if "__compiled__" in globals():
            logger.debug("Running in a Nuitka bundle")
            providers_dir = Path(sys.executable).parent / "providers"
        else:
            providers_dir = Path(__file__).parent.parent / "providers"
        logger.debug(f"Base providers path: {providers_dir}")
        for file in providers_dir.glob("*.py"):
            if file.name.startswith("__"):
                continue
            if file.name == "base.py":
                continue
            logger.debug(f"Found {file.name}")

            module_name = f"src.providers.{file.stem}"
            try:
                # 延迟导入，避免在加载时就初始化COM
                module = importlib.import_module(module_name)
                # 获取模块中的 ProviderMeta
                meta = getattr(module, "__meta__", None)
                if meta and isinstance(meta, ProviderMeta):
                    # 查找 Provider 类
                    provider_class = None
                    provider_gui_class = None
                    for _, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, IProvider)
                            and obj is not IProvider
                        ):
                            provider_class = obj
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, IProviderSettingGUI)
                            and obj is not IProviderSettingGUI
                        ):
                            provider_gui_class = obj
                        if (
                            provider_class is not None
                            and provider_gui_class is not None
                        ):
                            break
                    if provider_class:
                        self.register_provider(
                            meta.provider_name, meta, provider_class, provider_gui_class
                        )
                        logger.success(
                            f"Successfully loaded provider: {meta.provider_name}"
                        )
                    else:
                        logger.error(
                            f"Failed to load provider: {meta.provider_name} - Can't find Provider class"
                        )
            except Exception as e:
                logger.error(f"Failed to load provider file: {file.stem} - {str(e)}")
                # 继续加载其他provider，不要因为一个失败就停止
                continue

    def get_provider_setting_gui_class(
        self, provider_name: str
    ) -> Optional[type[IProviderSettingGUI]]:
        return self.providers_guis.get(provider_name)

    def get_provider_class(self, provider_name: str) -> Optional[type[IProvider]]:
        return self.providers.get(provider_name)

    def get_provider_meta(self, provider_name: str) -> Optional[IProviderMeta]:
        return self.provider_metas.get(provider_name)

    def get_all_provider_names(self) -> List[str]:
        return list(self.providers.keys())


class ProviderFactory(IProviderFactory):
    inputDone = Signal()

    @property
    def provider_instances(self) -> dict[str, IProvider]:
        return self._provider_instances

    def __init__(self, registry: IProviderRegistry, context: IProviderContext):
        super().__init__()
        self.registry = registry
        self.context = context
        self.thread_pool = QThreadPool.globalInstance()
        self._provider_instances: dict[str, IProvider] = {}
        self._mutex = QMutex()

    def create_instance(
        self, provider_name: str, provider_context: IProviderContext | None = None
    ) -> IProvider:
        if provider_context is None:
            provider_context = self.context

        # 虽然感觉不会产生竞态，但还是加个锁比较好
        with QMutexLocker(self._mutex):
            if self.provider_instances.get(provider_name) is None:
                self.provider_instances[provider_name] = (
                    self.registry.get_provider_class(provider_name)(provider_context)
                )
                # 信号链
                self.provider_instances[provider_name].inputDone.connect(
                    self.inputDone.emit
                )
            return self.provider_instances[provider_name]

    def get_instance(self, provider_name: str) -> IProvider | None:
        # 虽然感觉不会产生竞态，但还是加个锁比较好
        with QMutexLocker(self._mutex):
            if self.provider_instances.get(provider_name) is None:
                return None
            return self.provider_instances[provider_name]


class ProviderManager(IProviderManager):
    inputDone = Signal()

    def __init__(self, registry: IProviderRegistry, factory: IProviderFactory):
        super().__init__()
        self.factory = factory
        self.registry = registry
        # 信号链
        self.factory.inputDone.connect(self.inputDone.emit)
        self.thread_pool = QThreadPool.globalInstance()

    def provider_launch(
        self, provider_name: str, provider_context: IProviderContext
    ) -> bool:
        instance = self.factory.create_instance(provider_name)
        worker = ProviderWorker(instance, "launch")
        self.thread_pool.start(worker)
        return True

    def provider_send_input(self, provider_name: str) -> None:
        instance = self.factory.create_instance(provider_name)
        worker = ProviderWorker(instance, "send_input")
        self.thread_pool.start(worker)

    def provider_cleanup(self, provider_name: str) -> None:
        instance = self.factory.create_instance(provider_name)
        if instance:
            worker = ProviderWorker(instance, "cleanup")
            self.thread_pool.start(worker)
            del self.factory.provider_instances[provider_name]

    def provider_run(self, provider_name: str, method: str):
        instance = self.factory.create_instance(provider_name)
        if instance:
            worker = ProviderWorker(instance, method)
            self.thread_pool.start(worker)
