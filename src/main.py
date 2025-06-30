import sys
from src.core.containers import MainContainer

if __name__ == "__main__":
    container = MainContainer()
    container.wire(modules=[__name__])

    app = container.qt_application()

    container.wiring()

    tray_icon = container.tray_icon()

    app_config = container.app_config()

    window_hook = container.window_hook()
    window_hook.set_provider_process_names_by_provider_name(
        app_config.data.Common.active_provider
    )

    container.window_hook_thread().start()
    container.keyboard_hook_thread().start()
    container.provider_manager_thread().start()

    tray_icon.show()

    sys.exit(app.exec())
