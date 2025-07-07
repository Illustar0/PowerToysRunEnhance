from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QApplication
from loguru import logger
from qfluentwidgets import setTheme

from src.core.interfaces import (
    IConfigurationService,
    ITrayIcon,
    IWindowHook,
    IKeyboardHook,
    IProviderManager,
    ITrayIconPresenter,
    IAggressiveDialog,
    IFluentWindow,
    INativeEventFilter,
)


def wire(
    app: QApplication,
    dialog: IAggressiveDialog,
    app_config: IConfigurationService,
    tray_icon: ITrayIcon,
    main_window: IFluentWindow,
    window_hook: IWindowHook,
    keyboard_hook: IKeyboardHook,
    provider_manager: IProviderManager,
    tray_icon_presenter: ITrayIconPresenter,
    native_event_filter: INativeEventFilter,
    window_hook_thread: QThread,
    keyboard_hook_thread: QThread,
    provider_manager_thread: QThread,
):
    """这个函数负责连接所有组件的信号与槽"""

    # 1. 移动 Workers 到线程
    window_hook.moveToThread(window_hook_thread)
    keyboard_hook.moveToThread(keyboard_hook_thread)
    provider_manager.moveToThread(provider_manager_thread)

    # 2. 连接所有信号与槽
    # hook_worker connections
    window_hook.windowsSearchClosed.connect(keyboard_hook.on_windows_search_close)
    window_hook.providerStarted.connect(keyboard_hook.on_provider_started)
    window_hook.windowsSearchStarted.connect(keyboard_hook.start_listening)

    # 阻塞 抢夺焦点
    keyboard_hook.getFocus.connect(
        dialog.get_focus, type=Qt.ConnectionType.BlockingQueuedConnection
    )

    # provider_manager connections
    provider_manager.inputDone.connect(keyboard_hook.stop_listening)

    # tray_icon connections
    tray_icon.enable_changed.connect(keyboard_hook.set_enabled)
    tray_icon.enable_changed.connect(window_hook.set_enabled)
    tray_icon.activated.connect(main_window.on_tray_icon_activated)

    tray_icon_presenter.reset_status.connect(keyboard_hook.stop_listening)

    # NativeEventFilter
    native_event_filter.themeChanged.connect(setTheme)
    native_event_filter.themeChanged.connect(tray_icon_presenter.on_theme_changed)

    # 线程启动连接
    window_hook_thread.started.connect(window_hook.set_hook)

    # 应用退出清理
    app.aboutToQuit.connect(window_hook.unset_hook)
    app.aboutToQuit.connect(window_hook_thread.quit)
    app.aboutToQuit.connect(keyboard_hook_thread.quit)
    app.aboutToQuit.connect(provider_manager_thread.quit)

    # 确保线程完全退出
    app.aboutToQuit.connect(window_hook_thread.wait)
    app.aboutToQuit.connect(keyboard_hook_thread.wait)
    app.aboutToQuit.connect(provider_manager_thread.wait)

    logger.debug("Successfully to wire components.")
