import sys

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
from dependency_injector import containers, providers

from src.core.hook import WindowHookWorker, KeyboardHookWorker
from src.core.model import ApplicationModel, ConfigurationService
from src.core.models import ProviderContext
from src.core.presenter import TrayIconPresenter, NativeEventFilter
from src.core.provider_manager import ProviderManager, ProviderRegistry, ProviderFactory
from src.core.wiring import wire
from src.ui.main import MainWindow
from src.ui.tray_icon import TrayIcon
from src.utils import AggressiveDialog


class MainContainer(containers.DeclarativeContainer):
    app_config = providers.Singleton(
        ConfigurationService,
        config_path="./config.toml",
    )
    app = providers.Singleton(ApplicationModel, config_service=app_config)

    provider_context = providers.Singleton(ProviderContext)
    provider_registry = providers.Singleton(
        ProviderRegistry,
    )
    provider_factory = providers.Factory(
        ProviderFactory, registry=provider_registry, context=provider_context
    )
    provider_manager = providers.Singleton(
        ProviderManager, registry=provider_registry, factory=provider_factory
    )

    # UI
    tray_icon = providers.Singleton(TrayIcon)
    main_window = providers.Singleton(MainWindow)

    # Worker
    window_hook = providers.Singleton(
        WindowHookWorker,
        provider_manager=provider_manager,
        provider_registry=provider_registry,
    )
    keyboard_hook = providers.Singleton(
        KeyboardHookWorker,
        app_config=app_config,
        provider_registry=provider_registry,
        provider_manager=provider_manager,
        provider_context=provider_context,
    )
    provider_manager = provider_manager

    # Presenter
    native_event_filter = providers.Singleton(NativeEventFilter)
    tray_icon_presenter = providers.Singleton(
        TrayIconPresenter, application_model=app, tray_icon=tray_icon
    )

    # Thread
    keyboard_hook_thread = providers.Singleton(QThread)
    window_hook_thread = providers.Singleton(QThread)
    provider_manager_thread = providers.Singleton(QThread)

    # Main
    qt_application = providers.Singleton(QApplication, sys.argv)

    # 用来抢夺焦点
    dialog = providers.Singleton(AggressiveDialog)

    # Wire
    wiring = providers.Callable(
        wire,
        app=qt_application,
        dialog=dialog,
        app_config=app_config,
        tray_icon=tray_icon,
        main_window=main_window,
        window_hook=window_hook,
        keyboard_hook=keyboard_hook,
        provider_manager=provider_manager,
        tray_icon_presenter=tray_icon_presenter,
        native_event_filter=native_event_filter,
        window_hook_thread=window_hook_thread,
        keyboard_hook_thread=keyboard_hook_thread,
        provider_manager_thread=provider_manager_thread,
    )
