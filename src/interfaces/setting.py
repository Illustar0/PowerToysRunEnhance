from os import PathLike
import winput
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from qfluentwidgets import (
    CardWidget,
    FluentIcon,
    PrimaryPushButton,
    TransparentToolButton,
    TitleLabel,
    MessageBoxBase,
    CaptionLabel,
    BodyLabel,
    SwitchButton,
    LineEdit,
)
from tomlkit import toml_file
from winput import WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP

from .base import BaseCard

VK_TO_KEY_NAME = {
    # 修饰键
    "VK_LMENU": "Alt",
    "VK_RMENU": "Alt",
    "VK_MENU": "Alt",
    "VK_LCONTROL": "Ctrl",
    "VK_RCONTROL": "Ctrl",
    "VK_CONTROL": "Ctrl",
    "VK_LSHIFT": "Shift",
    "VK_RSHIFT": "Shift",
    "VK_SHIFT": "Shift",
    "VK_LWIN": "Win",
    "VK_RWIN": "Win",
    # 功能键
    "VK_F1": "F1",
    "VK_F2": "F2",
    "VK_F3": "F3",
    "VK_F4": "F4",
    "VK_F5": "F5",
    "VK_F6": "F6",
    "VK_F7": "F7",
    "VK_F8": "F8",
    "VK_F9": "F9",
    "VK_F10": "F10",
    "VK_F11": "F11",
    "VK_F12": "F12",
    # 字母键
    "VK_A": "A",
    "VK_B": "B",
    "VK_C": "C",
    "VK_D": "D",
    "VK_E": "E",
    "VK_F": "F",
    "VK_G": "G",
    "VK_H": "H",
    "VK_I": "I",
    "VK_J": "J",
    "VK_K": "K",
    "VK_L": "L",
    "VK_M": "M",
    "VK_N": "N",
    "VK_O": "O",
    "VK_P": "P",
    "VK_Q": "Q",
    "VK_R": "R",
    "VK_S": "S",
    "VK_T": "T",
    "VK_U": "U",
    "VK_V": "V",
    "VK_W": "W",
    "VK_X": "X",
    "VK_Y": "Y",
    "VK_Z": "Z",
    # 数字键
    "VK_0": "0",
    "VK_1": "1",
    "VK_2": "2",
    "VK_3": "3",
    "VK_4": "4",
    "VK_5": "5",
    "VK_6": "6",
    "VK_7": "7",
    "VK_8": "8",
    "VK_9": "9",
    # 方向键
    "VK_UP": "Up",
    "VK_DOWN": "Down",
    "VK_LEFT": "Left",
    "VK_RIGHT": "Right",
    # 特殊键
    "VK_SPACE": "Space",
    "VK_RETURN": "Enter",
    "VK_ESCAPE": "Esc",
    "VK_TAB": "Tab",
    "VK_BACK": "Backspace",
    "VK_DELETE": "Delete",
    "VK_INSERT": "Insert",
    "VK_HOME": "Home",
    "VK_END": "End",
    "VK_PRIOR": "Page Up",
    "VK_NEXT": "Page Down",
    "VK_CAPITAL": "Caps Lock",
    "VK_NUMLOCK": "Num Lock",
    "VK_SCROLL": "Scroll Lock",
    "VK_PAUSE": "Pause",
    "VK_SNAPSHOT": "Print Screen",
    # 数字键盘
    "VK_NUMPAD0": "Num 0",
    "VK_NUMPAD1": "Num 1",
    "VK_NUMPAD2": "Num 2",
    "VK_NUMPAD3": "Num 3",
    "VK_NUMPAD4": "Num 4",
    "VK_NUMPAD5": "Num 5",
    "VK_NUMPAD6": "Num 6",
    "VK_NUMPAD7": "Num 7",
    "VK_NUMPAD8": "Num 8",
    "VK_NUMPAD9": "Num 9",
    "VK_MULTIPLY": "Num *",
    "VK_ADD": "Num +",
    "VK_SUBTRACT": "Num -",
    "VK_DECIMAL": "Num .",
    "VK_DIVIDE": "Num /",
    # 其他常用符号键
    "VK_OEM_PLUS": "+",
    "VK_OEM_MINUS": "-",
    "VK_OEM_COMMA": ",",
    "VK_OEM_PERIOD": ".",
    "VK_OEM_1": ";",
    "VK_OEM_2": "/",
    "VK_OEM_3": "`",
    "VK_OEM_4": "[",
    "VK_OEM_5": "\\",
    "VK_OEM_6": "]",
    "VK_OEM_7": "'",
}


class BaseConfig(QObject):
    configChanged = Signal(str, object)

    def __init__(self, toml_file_path: str | PathLike[str]):
        super().__init__()
        self.toml_file_path = toml_file_path
        self.config = toml_file.TOMLFile(toml_file_path).read()

    def set(self, key, value):
        keys = key.split(".")
        target = self.config

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        last_key = keys[-1]
        target[last_key] = value

        self.save()

        # 发出信号
        self.configChanged.emit(key, value)

    def get(self, key, default=None):
        # 获取配置值，支持点号分隔的嵌套键
        keys = key.split(".")
        target = self.config

        for k in keys:
            if k not in target:
                return default
            target = target[k]

        return target

    def save(self):
        toml_file.TOMLFile(self.toml_file_path).write(self.config)


class Config(BaseConfig):
    def on_config_updated(self, params):
        if isinstance(params, tuple):
            self.set(params[1], params[0])


CONFIG = Config("config.toml")


class ShortcutCard(BaseCard):
    """快捷键设置卡片"""

    # 定义信号
    configUpdated = Signal(object)

    class ShortcutPicker(CardWidget):
        """FluentDesign 风格的快捷键选择卡片"""

        # 定义信号
        configUpdated = Signal(object)

        class ShortcutPickerMessageBox(MessageBoxBase):
            """自定义快捷键选择对话框"""

            # 定义信号
            configUpdated = Signal(object)

            def __init__(self, shortcut, extra_signal_params=None, parent=None):
                super().__init__(parent)
                self.keyButtons = []
                self.shortcut = shortcut
                self.extra_signal_params = extra_signal_params
                self.currentKeyIndex = 0
                self.keys = []

                # 初始化布局
                self.hBoxLayout = QHBoxLayout()
                self.titleLabel = BodyLabel("快捷键设置", self)
                self.tipLabel = CaptionLabel("PowerToys Run 的快捷键设置", self)
                self.tipLabel.setTextColor("#606060", "#d2d2d2")

                # 初始化按钮
                for key in self.shortcut.split("+"):
                    button = PrimaryPushButton(key, self)
                    self.keyButtons.append(button)
                    self.hBoxLayout.addWidget(button)
                    self.keys.append(key)

                # 将组件添加到布局中
                self.viewLayout.addWidget(self.titleLabel)
                self.viewLayout.addWidget(self.tipLabel)
                self.viewLayout.addLayout(self.hBoxLayout)

                # 设置对话框的最小宽度
                self.widget.setMinimumWidth(400)

                # 记录当前按下的键
                self.pressed_keys = list()

                # 设置键盘钩子
                winput.hook_keyboard(self.keyboardHookCallback)

            def keyboardHookCallback(self, event):
                key_name = winput.vk_code_dict.get(event.vkCode, "Unknown")
                original_pressed_keys = self.pressed_keys.copy()
                if event.action == WM_KEYDOWN or event.action == WM_SYSKEYDOWN:
                    self.pressed_keys.append(key_name)
                elif event.action == WM_KEYUP or event.action == WM_SYSKEYUP:
                    self.pressed_keys.remove(key_name)
                if len(self.pressed_keys) == 2:
                    winput.unhook_keyboard()
                    if self.extra_signal_params:
                        self.configUpdated.emit(
                            (
                                "+".join(
                                    [
                                        VK_TO_KEY_NAME.get(key)
                                        for key in self.pressed_keys
                                    ]
                                ),
                                self.extra_signal_params,
                            )
                        )
                        self.shortcut = "+".join(
                            [VK_TO_KEY_NAME.get(key) for key in self.pressed_keys]
                        )
                    else:
                        self.configUpdated.emit(
                            "+".join(
                                [VK_TO_KEY_NAME.get(key) for key in self.pressed_keys]
                            )
                        )
                if (
                    original_pressed_keys != self.pressed_keys
                    and len(self.pressed_keys) != 0
                ):
                    self.updateKeyButtons()

            def updateKeyButtons(self):
                # 创建新按钮但不立即显示
                new_buttons = []
                for key in self.pressed_keys:
                    button = PrimaryPushButton(VK_TO_KEY_NAME.get(key), self)
                    button.hide()  # 先隐藏
                    new_buttons.append(button)
                    self.hBoxLayout.addWidget(button)
                # 先添加，再移除
                for button in new_buttons:
                    self.hBoxLayout.addWidget(button)

                # 移除旧按钮
                for button in self.keyButtons:
                    self.hBoxLayout.removeWidget(button)
                    button.setParent(None)
                    button.deleteLater()

                # 显示新按钮
                for button in new_buttons:
                    button.show()

                self.keyButtons = new_buttons
                self.hBoxLayout.update()

        def __init__(self, shortcut, extra_signal_params=None, parent=None):
            super().__init__(parent)
            # self.setFixedHeight(90)
            self.new_shortcut_params = None
            self.KeyButton = []
            self.shortcut = shortcut
            self.extra_signal_params = extra_signal_params
            self.hBoxLayout = QHBoxLayout()
            self.vBoxLayout = QVBoxLayout()
            for key in self.shortcut.split("+"):
                button = PrimaryPushButton(key, self)
                button.clicked.connect(self.on_button_clicked)
                self.hBoxLayout.addWidget(button)
            self.editButton = TransparentToolButton(FluentIcon.EDIT, self)
            self.editButton.clicked.connect(self.on_button_clicked)
            self.hBoxLayout.addWidget(self.editButton)
            self.setLayout(self.hBoxLayout)

        def update_buttons(self, new_shortcut_key):
            for i in range(self.hBoxLayout.count()):
                self.hBoxLayout.itemAt(i).widget().deleteLater()
            self.KeyButton.clear()
            for key in new_shortcut_key.split("+"):
                button = PrimaryPushButton(key, self)
                button.clicked.connect(self.on_button_clicked)
                self.hBoxLayout.addWidget(button)
            self.editButton = TransparentToolButton(FluentIcon.EDIT, self)
            self.editButton.clicked.connect(self.on_button_clicked)
            self.hBoxLayout.addWidget(self.editButton)

        def handle_signal(self, params):
            """暂存快捷键更改"""
            if isinstance(params, tuple):
                self.new_shortcut_params = params

        def on_button_clicked(self):
            shortCutMessageBox = self.ShortcutPickerMessageBox(
                self.shortcut, self.extra_signal_params, self.window()
            )
            shortCutMessageBox.configUpdated.connect(self.handle_signal)
            if shortCutMessageBox.exec():
                self.configUpdated.emit(self.new_shortcut_params)
                self.update_buttons(self.new_shortcut_params[0])
            winput.unhook_keyboard()

    def __init__(
        self,
        title: str,
        content: str,
        icon: FluentIcon,
        default_value: str,
        extra_signal_params=None,
    ):
        super().__init__(title, content, icon)

        # 创建快捷键编辑器

        shortcutPicker = self.ShortcutPicker(default_value, extra_signal_params, self)
        shortcutPicker.configUpdated.connect(self.configUpdated)
        self.hBoxLayout.addWidget(shortcutPicker)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)


class AutoFocusCard(BaseCard):
    """AutoFocus 设置卡片"""

    # 定义信号
    configUpdated = Signal(object)

    def __init__(
        self,
        title: str,
        content: str,
        icon: FluentIcon,
        default_value: bool,
        extra_signal_params=None,
    ):
        super().__init__(title, content, icon)
        self.extra_signal_params = extra_signal_params
        # 创建快捷键编辑器

        switchButton = SwitchButton(self)
        switchButton.setChecked(default_value)
        switchButton.checkedChanged.connect(self.on_checked_changed)
        self.hBoxLayout.addWidget(switchButton)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    def on_checked_changed(self, checked):
        if self.extra_signal_params:
            self.configUpdated.emit((checked, self.extra_signal_params))
        else:
            self.configUpdated.emit(checked)


class FluentDivider(QFrame):
    def __init__(self, parent=None, is_horizontal=True, light_theme=True):
        super().__init__(parent)
        self.is_horizontal = is_horizontal
        self.light_theme = light_theme

        if is_horizontal:
            self.setFixedHeight(1)
            self.setMinimumWidth(1)
        else:
            self.setFixedWidth(1)
            self.setMinimumHeight(1)

        self.setContentsMargins(0, 0, 0, 0)
        self.setObjectName("fluentDivider")
        self.updateStyle()

    def updateStyle(self):
        if self.light_theme:
            divider_color = "#E1E1E1"  # 浅色主题的分隔线
        else:
            divider_color = "#333333"  # 深色主题的分隔线

        self.setStyleSheet(f"""
            #fluentDivider {{
                background-color: {divider_color};
                border: none;
                margin: {8 if self.is_horizontal else 0}px {0 if self.is_horizontal else 8}px;
            }}
        """)

    def setLightTheme(self, light_theme):
        self.light_theme = light_theme
        self.updateStyle()


class SearchWindowNameCard(BaseCard):
    """AutoFocus 设置卡片"""

    # 定义信号
    configUpdated = Signal(object)

    def __init__(
        self,
        title: str,
        content: str,
        icon: FluentIcon,
        default_value: str,
        extra_signal_params=None,
    ):
        super().__init__(title, content, icon)
        self.extra_signal_params = extra_signal_params
        # 创建快捷键编辑器

        self.lineEdit = LineEdit(self)
        self.lineEdit.setText(default_value)
        self.lineEdit.textEdited.connect(self.on_checked_changed)
        self.hBoxLayout.addWidget(self.lineEdit)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    def on_checked_changed(self):
        if self.extra_signal_params:
            self.configUpdated.emit((self.lineEdit.text(), self.extra_signal_params))
        else:
            self.configUpdated.emit(self.lineEdit.text())


class SettingInterface(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", "-"))
        self.vBoxLayout = QVBoxLayout()
        self.vBoxLayout.setContentsMargins(10, 20, 10, 20)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vBoxLayout)  # 设置主布局
        self.vBoxLayout.addWidget(TitleLabel("设置", self))
        searchWindowNameCard = SearchWindowNameCard(
            title="Windows 搜索窗口名",
            content="设置 Windows 搜索的窗口名",
            icon=FluentIcon.LABEL,
            default_value=CONFIG.get("settings.searchWindowName"),
            extra_signal_params="settings.searchWindowName",
        )
        searchWindowNameCard.configUpdated.connect(CONFIG.on_config_updated)
        self.vBoxLayout.addWidget(FluentDivider())
        self.vBoxLayout.addWidget(searchWindowNameCard)
        shortcutCard = ShortcutCard(
            title="PowerToys Run 快捷键",
            content="PowerToys Run 的快捷键设置",
            icon=FluentIcon.LABEL,
            default_value=CONFIG.get("settings.powerToysRunShortCut"),
            extra_signal_params="settings.powerToysRunShortCut",
        )
        shortcutCard.configUpdated.connect(CONFIG.on_config_updated)
        self.vBoxLayout.addWidget(FluentDivider())
        self.vBoxLayout.addWidget(shortcutCard)
        autoFocusCard = AutoFocusCard(
            title="自动设置焦点",
            content="是否自动为 PowerToys Run 窗口设置焦点",
            icon=FluentIcon.LABEL,
            default_value=CONFIG.get("settings.autoFocus"),
            extra_signal_params="settings.autoFocus",
        )
        autoFocusCard.configUpdated.connect(CONFIG.on_config_updated)
        self.vBoxLayout.addWidget(autoFocusCard)
