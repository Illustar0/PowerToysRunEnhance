import sys

from qfluentwidgets import setTheme, Theme

from src.core.containers import MainContainer

if __name__ == "__main__":
    # 在容器初始化前就设置主题
    setTheme(Theme.AUTO)

    container = MainContainer()
    container.wire(modules=[__name__])

    app = container.qt_application()
    if app.is_running:
        sys.exit(0)
    container.wiring()

    native_event_filter = container.native_event_filter()
    tray_icon = container.tray_icon()
    main_window = container.main_window()

    app_config = container.app_config()

    app.installNativeEventFilter(native_event_filter)

    window_hook = container.window_hook()
    window_hook.set_provider_process_names_by_provider_name(
        app_config.data.Common.active_provider
    )

    container.window_hook_thread().start()
    container.keyboard_hook_thread().start()
    container.provider_manager_thread().start()

    tray_icon.show()
    # 默认不显示主界面
    # main_window.show()

    sys.exit(app.exec())
