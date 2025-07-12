import sys
import threading

from PySide6.QtCore import QTimer
from PySide6.QtGui import QDesktopServices
from qfluentwidgets import (
    setTheme,
    Theme,
    setThemeColor,
    FluentIcon,
    NavigationAvatarWidget,
    NavigationItemPosition,
)
from qframelesswindow.utils import getSystemAccentColor

from src.core.constants import VERSION, APP_ID, APP_NAME
from src.core.containers import MainContainer
from src.utils import get_base_path, register_aumid

if __name__ == "__main__":
    # 在容器初始化前就设置主题
    setTheme(Theme.AUTO)

    # 设置主题色
    if sys.platform in ["win32", "darwin"]:
        setThemeColor(getSystemAccentColor())

    container = MainContainer()
    container.wire(modules=[__name__])

    app = container.qt_application()
    app_model = container.app_model()
    version_update_service = container.version_update_service()
    provider_registry = container.provider_registry()
    if app.is_running:
        sys.exit(0)

    native_event_filter = container.native_event_filter()
    tray_icon = container.tray_icon()
    main_interface = container.main_interface()
    main_interface.init_ui()

    setting_interface = container.setting_interface()
    provider_setting_card_groups_dict = {}
    for _, meta in provider_registry.get_provider_metas().items():
        provider_setting_card_groups_dict.update(
            {meta.provider_name_tr: meta.setting_group}
        )
    setting_interface.init_ui(provider_setting_card_groups_dict, VERSION)
    main_window = container.main_window()

    container.wiring()

    # 主窗口
    main_window.addSubInterface(main_interface, FluentIcon.HOME, "Dash")
    main_window.addSubInterface(
        setting_interface,
        FluentIcon.SETTING,
        "Settings",
    )
    main_window.navigationInterface.addSeparator()

    avatar = NavigationAvatarWidget(
        "Illustar0", str(get_base_path() / "resources" / "Avatar.png")
    )
    avatar.clicked.connect(
        lambda: QDesktopServices.openUrl("https://github.com/Illustar0")
    )

    main_window.navigationInterface.addWidget(
        routeKey="Avatar",
        widget=avatar,
        position=NavigationItemPosition.BOTTOM,
    )

    app_config = container.app_config()

    app.installNativeEventFilter(native_event_filter)

    window_hook = container.window_hook()

    container.window_hook_thread().start()
    container.keyboard_hook_thread().start()
    container.provider_manager_thread().start()

    register_aumid(APP_ID, APP_NAME, get_base_path() / "resources" / "logo.ico")
    QTimer.singleShot(10000, lambda: version_update_service.check_update(VERSION))

    tray_icon.show()
    # 默认不显示主界面
    # main_window.show()

    sys.exit(app.exec())
