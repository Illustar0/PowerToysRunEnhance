from enum import Enum
from typing import Union, Callable, Any, Iterable

import win32con
import win32gui
from PySide6.QtCore import (
    Qt,
    Signal,
    QRectF,
    Slot,
)
from PySide6.QtGui import (
    QIcon,
    QColor,
    QPainter,
    QFont,
    QPen,
    QRadialGradient,
    QLinearGradient,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QWidget,
    QPushButton,
)
from loguru import logger
from pynput import keyboard
from qfluentwidgets import (
    FluentIconBase,
    BodyLabel,
    SwitchButton,
    IndicatorPosition,
    HyperlinkButton,
    PushButton,
    TransparentToolButton,
    FluentIcon,
    PrimaryPushButton,
    isDarkTheme,
    FluentStyleSheet,
    setFont,
    MaskDialogBase,
    setCustomStyleSheet,
    CaptionLabel,
    Theme,
    getIconColor,
    PrimaryToolButton,
    DoubleSpinBox,
    ComboBox,
    CardWidget,
)

from src.core.interfaces import (
    ISettingCard,
    ISettingCardGroup,
    FluentCard,
)
from src.utils import vk_code_to_char, get_base_path


# 大量代码来自 qfluentwidgets


class FluentIconExpand(FluentIconBase, Enum):
    """Extended Fluent icon collection.

    This class extends the base Fluent icon set with custom icons
    specific to the Windows Search Utility application.

    :ivar WINDOWS: Windows logo icon
    :ivar KEYBOARD: Keyboard icon
    """

    WINDOWS = "Windows"
    KEYBOARD = "Keyboard"

    def path(self, theme=Theme.AUTO):
        """Get the file path for the icon based on the current theme.

        :param theme: Theme to use for icon selection
        :type theme: Theme

        :return: Path to the icon file
        :rtype: str
        """
        # getIconColor() 根据主题返回字符串 "white" 或者 "black"
        return str(
            get_base_path()
            / "resources"
            / "icons"
            / f"{self.value}_{getIconColor(theme)}.svg"
        )


class SettingCardGroup(ISettingCardGroup):
    """Setting card group container widget.

    This widget groups multiple setting cards together with a title label.
    It provides a consistent layout and styling for organizing related
    configuration options in the settings interface.

    :param title: Title text for the group
    :type title: str
    :param parent: Parent widget
    :type parent: QWidget, optional
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)
        self._settingCardList = []
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = QVBoxLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setSpacing(2)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout)
        self.vBoxLayout.addStretch(1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        setFont(self.titleLabel, 20)
        self.titleLabel.adjustSize()

    def addSettingCard(self, card: QWidget):
        """Add a single setting card to the group.

        :param card: Setting card widget to add
        :type card: QWidget
        """
        card.setParent(self)
        self._settingCardList.append(card)
        self.cardLayout.addWidget(card)
        self.adjustSize()

    def addSettingCards(self, cards: list[QWidget]):
        """Add multiple setting cards to the group.

        :param cards: List of setting card widgets to add
        :type cards: list[QWidget]
        """
        for card in cards:
            self.addSettingCard(card)

    def adjustSize(self):
        """Adjust the size of the group to fit all cards.

        :return: New size of the widget
        :rtype: QSize
        """
        h = self.cardLayout.heightForWidth(self.width()) + 46
        return self.resize(self.width(), h)

    def listSettingCard(self) -> list:
        """Get the list of setting cards in this group.

        :return: List of setting cards
        :rtype: list
        """
        return self._settingCardList


class SettingCard(ISettingCard):
    """Base setting card widget.

    This is the foundation class for all setting cards in the application.
    It provides a consistent layout with an icon, title, content text, and
    space for additional controls on the right side.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param title: Main title text
    :type title: str
    :param content: Optional description text below title
    :type content: str, optional
    :param parent: Parent widget
    :type parent: QWidget, optional
    """

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        content=None,
        config_path: str | None = None,
        parent=None,
    ):
        super().__init__(icon, title, content=content, parent=parent)

    def setTitle(self, title: str):
        """Set the title text of the card.

        :param title: New title text
        :type title: str
        """
        self.titleLabel.setText(title)

    def setContent(self, content: str):
        """Set the content text of the card.

        :param content: New content text
        :type content: str
        """
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def setValue(self, value):
        """Set the value of the configuration item.

        This method should be overridden by subclasses to handle
        specific value types and UI updates.

        :param value: Value to set
        :type value: Any
        """
        pass

    def setIconSize(self, width: int, height: int):
        """Set the icon size.

        :param width: Icon width in pixels
        :type width: int
        :param height: Icon height in pixels
        :type height: int
        """
        self.iconLabel.setFixedSize(width, height)

    def paintEvent(self, e):
        """Paint the card with rounded corners and theme-appropriate styling.

        :param e: Paint event
        :type e: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

    @property
    def configPath(self):
        return self._configPath


class SwitchCard(SettingCard):
    """Setting card with a switch button control.

    This card extends SettingCard to provide a toggle switch for boolean
    configuration values. It emits signals when the switch state changes
    and can be bound to configuration paths for automatic updates.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param title: Main title text
    :type title: str
    :param content: Optional description text
    :type content: str, optional
    :param config_path: Configuration path for automatic updates
    :type config_path: str, optional
    :param parent: Parent widget
    :type parent: QWidget, optional

    :signal checkedChanged: Emitted when switch state changes (config_path, bool)
    :signal valueChanged: Emitted when value changes (config_path, bool)
    """

    checkedChanged = Signal(str, bool)
    valueChanged = Signal(object, bool)

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        content: str = None,
        config_path: str = None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)

        self._configPath = config_path
        self.switchButton = SwitchButton(self.tr("Off"), self, IndicatorPosition.RIGHT)

        # add switch button to layout
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)

    def __onCheckedChanged(self, isChecked: bool):
        """Handle switch button state change.

        :param isChecked: New checked state
        :type isChecked: bool

        :emits checkedChanged: When switch state changes
        :emits valueChanged: When switch state changes
        """
        self.checkedChanged.emit(self._configPath, isChecked)
        self.valueChanged.emit(self._configPath, isChecked)

    def setValue(self, isChecked: bool):
        """Set the switch state and update the button text.

        :param isChecked: New checked state
        :type isChecked: bool
        """
        self.switchButton.setChecked(isChecked)
        self.switchButton.setText(self.tr("On") if isChecked else self.tr("Off"))

    def setChecked(self, isChecked: bool):
        """Set the checked state of the switch.

        :param isChecked: New checked state
        :type isChecked: bool
        """
        self.setValue(isChecked)

    def isChecked(self):
        """Get the current checked state of the switch.

        :return: Current checked state
        :rtype: bool
        """
        return self.switchButton.isChecked()


class HyperLinkCard(FluentCard):
    """Setting card with a hyperlink button.

    This card extends SettingCard to provide a clickable hyperlink button
    that can open URLs or trigger custom actions. Useful for settings that
    need to link to external resources or documentation.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param url: URL to open when the link is clicked
    :type url: str
    :param urlText: Text to display on the hyperlink button
    :type urlText: str
    :param title: Main title text
    :type title: str
    :param content: Optional description text
    :type content: str, optional
    :param parent: Parent widget
    :type parent: QWidget, optional

    :signal clicked: Emitted when the hyperlink is clicked
    """

    clicked = Signal()

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        url: str,
        urlText: str,
        title: str,
        content: str = None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)

        self.linkButton = HyperlinkButton(url, urlText, self)
        self.linkButton.clicked.connect(self.clicked.emit)

        self.hBoxLayout.addWidget(self.linkButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class PushCard(FluentCard):
    """Setting card with a push button control.

    This card extends SettingCard to provide a clickable push button
    for actions that don't require state management. Useful for triggering
    one-time actions or opening dialogs.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param text: Text to display on the push button
    :type text: str
    :param title: Main title text
    :type title: str
    :param content: Optional description text
    :type content: str, optional
    :param parent: Parent widget
    :type parent: QWidget, optional

    :signal clicked: Emitted when the button is clicked
    """

    clicked = Signal()

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        title: str,
        content: str | None = None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)

        self.button = PushButton(text, self)
        self.button.clicked.connect(self.clicked)

        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)


class PrimaryPushCard(PushCard):
    """Push setting card with primary color styling.

    This card extends PushCard to provide a primary-colored push button
    for important actions. The button uses the application's primary theme
    color to draw attention to key functionality.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param text: Text to display on the push button
    :type text: str
    :param title: Main title text
    :type title: str
    :param content: Optional description text
    :type content: str, optional
    :param parent: Parent widget
    :type parent: QWidget, optional
    """

    primaryButtonLightQss = """
        #primaryButton {
            color: white;
            background-color: --ThemeColorPrimary;
            border: 1px solid --ThemeColorLight1;
            border-bottom: 1px solid --ThemeColorDark1;
            padding: 5px 12px 5px 12px;
            outline: none;
        }

        #primaryButton:hover {
            background-color: --ThemeColorLight1;
            border: 1px solid --ThemeColorLight2;
            border-bottom: 1px solid --ThemeColorDark1;
        }
        
        #primaryButton:pressed {
            color: rgba(255, 255, 255, 0.63);
            background-color: --ThemeColorLight3;
            border: 1px solid --ThemeColorLight3;
        }
    """

    primaryButtonDarkQss = """
        #primaryButton {
            color: black;
            background-color: --ThemeColorPrimary;
            border: 1px solid --ThemeColorLight1;
            border-bottom: 1px solid --ThemeColorLight2;
            padding: 5px 12px 5px 12px;
            outline: none;
        }

        #primaryButton:hover {
            background-color: --ThemeColorDark1;
            border: 1px solid --ThemeColorLight1;
            border-bottom: 1px solid --ThemeColorLight2;
        }
        
        #primaryButton:pressed {
            color: rgba(0, 0, 0, 0.63);
            background-color: --ThemeColorDark2;
            border: 1px solid --ThemeColorDark2;
        }
    """

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        text: str,
        title: str,
        content: str | None = None,
        parent=None,
    ):
        super().__init__(icon, text, title, content, parent)
        self.button.setObjectName("primaryButton")
        setCustomStyleSheet(
            self.button, self.primaryButtonLightQss, self.primaryButtonDarkQss
        )


class DoubleSpinCard(SettingCard):
    """Setting card with a double spin box control.

    This card extends SettingCard to provide a spin box for floating-point
    numeric values. It supports range validation and emits signals when
    the value changes, making it suitable for numeric configuration settings.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param title: Main title text
    :type title: str
    :param content: Optional description text
    :type content: str, optional
    :param config_path: Configuration path for automatic updates
    :type config_path: str, optional
    :param parent: Parent widget
    :type parent: QWidget, optional

    :signal valueChanged: Emitted when value changes (config_path, float)
    """

    valueChanged = Signal(object, float)

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        content: str = None,
        config_path: str = None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        self._configPath = config_path

        self.doubleSpinBox = DoubleSpinBox()
        self.doubleSpinBox.valueChanged.connect(self._onDoubleSpinBoxValueChanged)

        self.hBoxLayout.addWidget(self.doubleSpinBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def setValue(self, value: float):
        """Set the current value of the spin box.

        :param value: New value to set
        :type value: float
        """
        self.doubleSpinBox.setValue(value)

    def setRange(self, min: float, max: float):
        """Set the valid range for the spin box.

        :param min: Minimum allowed value
        :type min: float
        :param max: Maximum allowed value
        :type max: float
        """
        self.doubleSpinBox.setRange(min, max)

    def _onDoubleSpinBoxValueChanged(self, new_value: float):
        """Handle spin box value changes.

        :param new_value: New value from the spin box
        :type new_value: float

        :emits valueChanged: When the value changes
        """
        self.valueChanged.emit(self._configPath, new_value)


class ComboBoxCard(SettingCard):
    """Setting card with a combo box control.

    This card extends SettingCard to provide a dropdown combo box for
    selecting from predefined options. It supports both text and icon
    items and can be bound to configuration paths for automatic updates.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param title: Main title text
    :type title: str
    :param content: Optional description text
    :type content: str, optional
    :param config_path: Configuration path for automatic updates
    :type config_path: str, optional
    :param parent: Parent widget
    :type parent: QWidget, optional

    :signal valueChanged: Emitted when selection changes (config_path, float)
    """

    valueChanged = Signal(object, int)

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        content: str = None,
        config_path: str = None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        self._configPath = config_path

        self.comboBox = ComboBox()
        self.comboBoxItemDict = {}
        self.comboBox.currentIndexChanged.connect(self._onComboBoxIndexChanged)

        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def setValue(self, value: int | str):
        """Set the current selected value.

        :param value: Index or text of the item to select
        :type value: int | str
        """
        if isinstance(value, str):
            value = list(self.comboBoxItemDict.keys()).index(value)
        self.comboBox.setCurrentIndex(value)

    def addItem(
        self,
        text: str,
        icon: str | QIcon | FluentIconBase | None = None,
        userData: Any = None,
    ):
        """Add an item to the combo box.

        :param text: Display text for the item
        :type text: str
        :param icon: Optional icon for the item
        :type icon: str | QIcon | FluentIconBase | None
        :param userData: Optional user data associated with the item
        :type userData: Any
        """
        self.comboBoxItemDict.update({text: userData})
        self.comboBox.addItem(text, icon, userData)

    def addItems(self, texts: Iterable[str]):
        """Add multiple text items to the combo box.

        :param texts: Iterable of text items to add
        :type texts: Iterable[str]
        """
        for text in texts:
            self.addItem(text)

    def _onComboBoxIndexChanged(self, new_value: int):
        """Handle combo box selection changes.

        :param new_value: New selected index
        :type new_value: float

        :emits valueChanged: When the selection changes
        """
        self.valueChanged.emit(self._configPath, new_value)


class ShortcutCard(SettingCard):
    """Setting card with keyboard shortcut configuration.

    This card extends SettingCard to provide a sophisticated keyboard shortcut
    configuration interface. It includes a visual shortcut picker and a dialog
    for capturing keyboard input with real-time validation.

    :param icon: Icon to display on the left side
    :type icon: Union[str, QIcon, FluentIconBase]
    :param title: Main title text
    :type title: str
    :param message_box_title: Title for the shortcut configuration dialog
    :type message_box_title: str
    :param content: Optional description text
    :type content: str, optional
    :param message_box_content: Optional content for the configuration dialog
    :type message_box_content: str, optional
    :param message_box_caption: Optional caption for the configuration dialog
    :type message_box_caption: str, optional
    :param config_path: Configuration path for automatic updates
    :type config_path: str, optional
    :param validate_func: Optional function to validate shortcut combinations
    :type validate_func: Callable[[str], bool], optional
    :param parent: Parent widget
    :type parent: QWidget, optional

    :signal shortcutChanged: Emitted when shortcut changes (str)
    :signal clicked: Emitted when shortcut picker is clicked
    :signal valueChanged: Emitted when shortcut value changes (config_path, str)
    """

    shortcutChanged = Signal(str)
    clicked = Signal()
    valueChanged = Signal(object, str)

    class ShortcutMessageBox(MaskDialogBase):
        """Modal dialog for capturing keyboard shortcuts.

        This dialog provides a user interface for capturing keyboard shortcuts
        with real-time validation and visual feedback. It uses low-level keyboard
        hooks to capture key combinations and displays them as interactive buttons.

        :param shortcut: Initial shortcut string
        :type shortcut: str
        :param title: Dialog title
        :type title: str
        :param content: Optional dialog content text
        :type content: str, optional
        :param caption: Optional dialog caption
        :type caption: str, optional
        :param validate_func: Optional validation function
        :type validate_func: Callable[[str], bool], optional
        :param parent: Parent widget
        :type parent: QWidget, optional

        :signal valueChanged: Emitted when shortcut value changes (str)
        :signal requestSetValue: Emitted to request UI update (str)
        """

        valueChanged = Signal(object)
        requestSetValue = Signal(str)
        primaryPushButtonDarkQss = """
                    PrimaryToolButton,
                    PrimaryToolButton:hover,
                    PrimaryToolButton:pressed,
                    PrimaryPushButton,
                    PrimaryPushButton:hover,
                    PrimaryPushButton:pressed {
                        color: black;
                        background-color: --ThemeColorPrimary;
                        border: 1px solid --ThemeColorLight1;
                        border-bottom: 1px solid --ThemeColorLight2;
                    }
                """
        primaryPushButtonLightQss = """
                    PrimaryToolButton,
                    PrimaryToolButton:hover,
                    PrimaryToolButton:pressed,
                    PrimaryPushButton,
                    PrimaryPushButton:hover,
                    PrimaryPushButton:pressed{
                        color: white;
                        background-color: --ThemeColorPrimary;
                        border: 1px solid --ThemeColorLight1;
                        border-bottom: 1px solid --ThemeColorDark1;
                    }
                """
        captionLabelLightQss = """
                    CaptionLabel {
                        color: #c8c8c8;
                    }    
                """
        invalidPrimaryPushButtonDarkQss = """
                    PrimaryToolButton,
                    PrimaryToolButton:hover,
                    PrimaryToolButton:pressed,
                    PrimaryPushButton,
                    PrimaryPushButton:hover,
                    PrimaryPushButton:pressed {
                        color: #ff99a4;
                        background-color: #442726;
                        border: 2px solid #ff99a4;
                        border-bottom: 2px solid #ff99a4;
                    }
                """
        invalidPrimaryPushButtonLightQss = """
                    PrimaryToolButton,
                    PrimaryToolButton:hover,
                    PrimaryToolButton:pressed,
                    PrimaryPushButton,
                    PrimaryPushButton:hover,
                    PrimaryPushButton:pressed{
                        color: #c42b1c;
                        background-color: #fde7e9;
                        border: 2px solid #c42b1c;
                        border-bottom: 2px solid #c42b1c;
                    }
                """

        def __init__(
            self,
            shortcut: str,
            title: str,
            content: str | None = None,
            caption: str | None = None,
            validate_func: Callable[[str], bool] | None = None,
            parent=None,
        ):
            super().__init__(parent=parent)
            self.buttonGroup = QFrame(self.widget)

            self.widget.setMinimumHeight(400)
            self.widget.setMinimumWidth(500)

            self.yesButton = PrimaryPushButton(self.tr("OK"), self.buttonGroup)
            self.resetButton = QPushButton(self.tr("Reset"), self.buttonGroup)
            self.cancelButton = QPushButton(self.tr("Cancel"), self.buttonGroup)

            self.vBoxLayout = QVBoxLayout(self.widget)
            self.viewLayout = QVBoxLayout()
            self.buttonLayout = QHBoxLayout(self.buttonGroup)

            self._initWidget()

            self.validateFunc = validate_func
            self.mainWindowHwnd = self.parent().winId()

            self.shortcutBackup = shortcut
            self.shortcutVkCodeBuffer = []
            self.shortcutCharBuffer = []
            self.hasKeyReleased = False

            self.requestSetValue.connect(self.setValue)

            titleLabelFont = QFont()
            titleLabelFont.setPointSize(15)

            titleLabel = BodyLabel(title, self)
            titleLabel.setFont(titleLabelFont)

            self.viewLayout.addWidget(titleLabel)
            if content is not None:
                contentLabel = BodyLabel(content, self)
                self.viewLayout.addWidget(contentLabel)
            self.viewLayout.addStretch(1)

            self.shortcutLayout = QHBoxLayout()
            self.shortcutLayout.addStretch(1)

            primaryPushButtonFont = QFont()
            primaryPushButtonFont.setPointSize(12)
            primaryPushButtonFont.setBold(True)

            for key in shortcut.split("+"):
                if key == "Win":
                    primaryPushButton = PrimaryToolButton(
                        FluentIconExpand.WINDOWS, self
                    )
                else:
                    primaryPushButton = PrimaryPushButton(key, self)
                primaryPushButton.setMinimumSize(55, 55)
                primaryPushButton.setFont(primaryPushButtonFont)

                # 去除悬停与点击变色
                setCustomStyleSheet(
                    primaryPushButton,
                    self.primaryPushButtonLightQss,
                    self.primaryPushButtonDarkQss,
                )

                self.shortcutLayout.addWidget(primaryPushButton)

            self.shortcutLayout.addStretch(1)
            self.viewLayout.addLayout(self.shortcutLayout)

            self.viewLayout.addStretch(1)

            if caption is not None:
                captionLabel = CaptionLabel(caption, self)
                captionLabel.setTextColor(
                    QColor.fromString("#616161"), QColor.fromString("#c2c2c2")
                )
                self.viewLayout.addWidget(captionLabel)

            # 键盘监听
            self.listener = keyboard.Listener(
                win32_event_filter=self._win32_event_filter
            )
            self.listener.start()

        def _initWidget(self):
            self._setQss()
            self._initLayout()

            self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
            self.setMaskColor(QColor(0, 0, 0, 76))

            # fixes https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/19
            self.yesButton.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)
            self.resetButton.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)
            self.cancelButton.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)

            self.yesButton.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)

            self.yesButton.setFocus()
            self.buttonGroup.setFixedHeight(81)

            self.yesButton.clicked.connect(self._onYesButtonClicked)
            self.resetButton.clicked.connect(self._onResetButtonClicked)
            self.cancelButton.clicked.connect(self._onCancelButtonClicked)

        def _initLayout(self):
            self._hBoxLayout.removeWidget(self.widget)
            self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignmentFlag.AlignCenter)

            self.vBoxLayout.setSpacing(0)
            self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
            self.vBoxLayout.addLayout(self.viewLayout, 1)
            self.vBoxLayout.addWidget(self.buttonGroup, 0, Qt.AlignmentFlag.AlignBottom)

            self.viewLayout.setSpacing(12)
            self.viewLayout.setContentsMargins(24, 24, 24, 24)

            self.buttonLayout.setSpacing(12)
            self.buttonLayout.setContentsMargins(24, 24, 24, 24)
            self.buttonLayout.addWidget(
                self.yesButton, 1, Qt.AlignmentFlag.AlignVCenter
            )
            self.buttonLayout.addWidget(
                self.resetButton, 1, Qt.AlignmentFlag.AlignVCenter
            )
            self.buttonLayout.addWidget(
                self.cancelButton, 1, Qt.AlignmentFlag.AlignVCenter
            )

        @Slot(str)
        def setValue(self, value):
            isValid = self.validateFunc(value)
            while self.shortcutLayout.count() > 0:
                item = self.shortcutLayout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()

            primaryPushButtonFont = QFont()
            primaryPushButtonFont.setPointSize(12)
            primaryPushButtonFont.setBold(True)

            self.shortcutLayout.addStretch(1)

            for key in value.split("+"):
                if key == "Win":
                    primaryPushButton = PrimaryToolButton(
                        FluentIconExpand.WINDOWS, self
                    )
                else:
                    primaryPushButton = PrimaryPushButton(key, self)
                primaryPushButton.setMinimumSize(55, 55)
                primaryPushButton.setFont(primaryPushButtonFont)

                # 去除悬停与点击变色
                if isValid:
                    setCustomStyleSheet(
                        primaryPushButton,
                        self.primaryPushButtonLightQss,
                        self.primaryPushButtonDarkQss,
                    )
                    self.yesButton.setEnabled(True)
                else:
                    setCustomStyleSheet(
                        primaryPushButton,
                        self.invalidPrimaryPushButtonLightQss,
                        self.invalidPrimaryPushButtonDarkQss,
                    )
                    self.yesButton.setEnabled(False)

                self.shortcutLayout.addWidget(primaryPushButton)

            self.shortcutLayout.addStretch(1)

            self.shortcutLayout.activate()
            self.widget.updateGeometry()
            self.widget.update()

        def validate(self, value: str) -> bool:
            if value.split("+")[0] not in ["Shift", "Win", "Alt"]:
                return False
            return True

        def _onCancelButtonClicked(self):
            self.listener.stop()
            self.reject()

        def _onResetButtonClicked(self):
            self.setValue(self.shortcutBackup)

        def _onYesButtonClicked(self):
            self.listener.stop()
            self.valueChanged.emit("+".join(self.shortcutCharBuffer))
            self.accept()

        def _win32_event_filter(self, msg, data):
            # 避免钩子影响到别的 APP
            if win32gui.GetForegroundWindow() != self.mainWindowHwnd:
                return

            if (
                msg
                in (
                    win32con.WM_KEYDOWN,
                    win32con.WM_SYSKEYDOWN,
                )
                and (data.flags & win32con.LLKHF_INJECTED) == 0
            ):
                if self.hasKeyReleased:
                    self.shortcutVkCodeBuffer = []
                    self.shortcutCharBuffer = []
                    self.hasKeyReleased = False

                if data.vkCode in self.shortcutVkCodeBuffer:
                    self.listener.suppress_event()

                self.shortcutVkCodeBuffer.append(data.vkCode)
                char = vk_code_to_char(data.vkCode)
                if char is None:
                    raise ValueError(f"Unknown Key: {data.vkCode}")
                else:
                    if len(char) == 1:
                        char = char.upper()
                self.shortcutCharBuffer.append(char)
                # 差点忘了这不是主线程
                # self.setValue("+".join(self.shortcutCharBuffer))
                logger.debug("+".join(self.shortcutCharBuffer))
                self.requestSetValue.emit("+".join(self.shortcutCharBuffer))
            elif (
                msg
                in (
                    win32con.WM_KEYUP,
                    win32con.WM_SYSKEYUP,
                )
                and (data.flags & win32con.LLKHF_INJECTED) == 0
            ):
                self.hasKeyReleased = True

            self.listener.suppress_event()

        def _setQss(self):
            self.buttonGroup.setObjectName("buttonGroup")
            self.resetButton.setObjectName("cancelButton")
            self.cancelButton.setObjectName("cancelButton")
            FluentStyleSheet.DIALOG.apply(self)

            # 给 buttonGroup 补上圆角
            qss = """
            #buttonGroup {
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            """
            setCustomStyleSheet(self, qss, qss)

    class ShortcutPicker(CardWidget):
        """Interactive widget for displaying and editing keyboard shortcuts.

        This widget displays keyboard shortcuts as a series of styled buttons
        and provides an edit button to open the shortcut configuration dialog.
        It uses custom painting to provide a modern, interactive appearance.

        :param parent: Parent widget
        :type parent: QWidget, optional

        :signal clicked: Emitted when the picker is clicked for editing
        """

        clicked = Signal()
        TransparentToolButtonQss = """
            TransparentToolButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
                margin: 0;
            }

            TransparentToolButton:hover,
            TransparentToolButton:pressed {
                background-color: transparent;
                border: none;
            }
        """
        primaryPushButtonDarkQss = """
            PrimaryToolButton,
            PrimaryToolButton:hover,
            PrimaryToolButton:pressed,
            PrimaryPushButton,
            PrimaryPushButton:hover,
            PrimaryPushButton:pressed {
                color: black;
                background-color: --ThemeColorPrimary;
                border: 1px solid --ThemeColorLight1;
                border-bottom: 1px solid --ThemeColorLight2;
            }
        """
        primaryPushButtonLightQss = """
            PrimaryToolButton,
            PrimaryToolButton:hover,
            PrimaryToolButton:pressed,
            PrimaryPushButton,
            PrimaryPushButton:hover,
            PrimaryPushButton:pressed{
                color: white;
                background-color: --ThemeColorPrimary;
                border: 1px solid --ThemeColorLight1;
                border-bottom: 1px solid --ThemeColorDark1;
            }
        """

        def __init__(self, parent=None):
            super().__init__(parent)
            self.hBoxLayout = QHBoxLayout()
            self.setLayout(self.hBoxLayout)

            self.editButton = TransparentToolButton(FluentIcon.EDIT, self)
            self.editButton.clicked.connect(self.clicked.emit)

            # 去除悬停与点击变色
            setCustomStyleSheet(
                self.editButton,
                self.TransparentToolButtonQss,
                self.TransparentToolButtonQss,
            )

            self.hBoxLayout.addWidget(self.editButton, 0, Qt.AlignmentFlag.AlignRight)

        def paintEvent(self, e):
            painter = QPainter(self)
            painter.setRenderHints(QPainter.RenderHint.Antialiasing)

            w, h = self.width(), self.height()
            r = self.borderRadius
            rect = self.rect().adjusted(1, 1, -1, -1)

            isDark = isDarkTheme()

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.backgroundColor)
            painter.drawRoundedRect(rect, r, r)

            pen = QPen()
            pen.setWidth(1)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

            if isDark:
                if self.isPressed:
                    borderColor = QColor(255, 255, 255, int(0.16 * 255))
                elif self.isHover:
                    borderColor = QColor(255, 255, 255, int(0.12 * 255))
                else:
                    borderColor = QColor(255, 255, 255, int(0.08 * 255))
            else:
                if self.isPressed:
                    borderColor = QColor(0, 0, 0, int(0.20 * 255))
                elif self.isHover:
                    borderColor = QColor(0, 0, 0, int(0.14 * 255))
                else:
                    borderColor = QColor(0, 0, 0, int(0.10 * 255))

            pen.setColor(borderColor)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            borderRect = QRectF(0.5, 0.5, w - 1, h - 1)
            painter.drawRoundedRect(borderRect, r, r)

            if self.isHover and not self.isPressed:
                # 微光渐变
                gradient = QLinearGradient(0, 0, w, 0)
                if isDark:
                    gradient.setColorAt(0, QColor(255, 255, 255, 0))
                    gradient.setColorAt(0.3, QColor(255, 255, 255, 5))
                    gradient.setColorAt(0.7, QColor(255, 255, 255, 5))
                    gradient.setColorAt(1, QColor(255, 255, 255, 0))
                else:
                    gradient.setColorAt(0, QColor(255, 255, 255, 0))
                    gradient.setColorAt(0.3, QColor(255, 255, 255, 15))
                    gradient.setColorAt(0.7, QColor(255, 255, 255, 15))
                    gradient.setColorAt(1, QColor(255, 255, 255, 0))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(gradient)
                painter.drawRoundedRect(rect, r, r)

            if self.isPressed:
                shadowGradient = QRadialGradient(w / 2, h / 2, max(w, h) / 2)
                if isDark:
                    shadowGradient.setColorAt(0, QColor(0, 0, 0, 0))
                    shadowGradient.setColorAt(0.8, QColor(0, 0, 0, 0))
                    shadowGradient.setColorAt(1, QColor(0, 0, 0, 8))
                else:
                    shadowGradient.setColorAt(0, QColor(0, 0, 0, 0))
                    shadowGradient.setColorAt(0.8, QColor(0, 0, 0, 0))
                    shadowGradient.setColorAt(1, QColor(0, 0, 0, 5))

                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(shadowGradient)
                painter.drawRoundedRect(rect, r, r)

        def _hoverBackgroundColor(self):
            isDark = isDarkTheme()
            if isDark:
                return QColor(255, 255, 255, int(0.04 * 255))
            else:
                return QColor(0, 0, 0, int(0.02 * 255))

        def _pressedBackgroundColor(self):
            isDark = isDarkTheme()
            if isDark:
                return QColor(255, 255, 255, int(0.03 * 255))
            else:
                return QColor(0, 0, 0, int(0.015 * 255))

        @property
        def backgroundColor(self):
            if self.isPressed:
                return self._pressedBackgroundColor()
            elif self.isHover:
                return self._hoverBackgroundColor()
            else:
                isDark = isDarkTheme()
                if isDark:
                    return QColor(255, 255, 255, int(0.04 * 255))
                else:
                    return QColor(255, 255, 255, int(0.7 * 255))

        def setValue(self, value: str):
            if self.hBoxLayout.count() != 1:
                while self.hBoxLayout.count() > 1:
                    item = self.hBoxLayout.takeAt(0)
                    widget = item.widget()
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()

            primaryPushButtonFont = QFont()
            primaryPushButtonFont.setPointSize(12)
            primaryPushButtonFont.setBold(True)

            for key in reversed(value.split("+")):
                if key == "Win":
                    button = PrimaryToolButton(FluentIconExpand.WINDOWS, self)
                else:
                    button = PrimaryPushButton(key, self)

                button.clicked.connect(self.clicked.emit)
                button.setFont(primaryPushButtonFont)

                # 去除悬停与点击变色
                setCustomStyleSheet(
                    button,
                    self.primaryPushButtonLightQss,
                    self.primaryPushButtonDarkQss,
                )

                self.hBoxLayout.insertWidget(0, button)

    def __init__(
        self,
        icon: Union[str, QIcon, "FluentIconBase"],
        title: str,
        message_box_title: str,
        content: str | None = None,
        message_box_content: str | None = None,
        message_box_caption: str | None = None,
        config_path: str | None = None,
        validate_func: Callable[[str], bool] | None = None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        self._configPath = config_path
        self.messageBoxTitle = message_box_title
        self.messageBoxContent = message_box_content
        self.messageBoxCaption = message_box_caption
        self.messageBoxValidateFunc = validate_func

        self.shortcut: str | None = None
        self.shortcutPicker = self.ShortcutPicker()
        self.shortcutPicker.clicked.connect(self._onShortcutPickerClicked)

        self.hBoxLayout.addWidget(self.shortcutPicker, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _onShortcutPickerClicked(self):
        """Handle shortcut picker click event.

        Opens the shortcut configuration dialog with current settings
        and connects the value change signal for updates.
        """
        shortCutMessageBox = self.ShortcutMessageBox(
            shortcut=self.shortcut,
            title=self.messageBoxTitle,
            content=self.messageBoxContent,
            caption=self.messageBoxCaption,
            validate_func=self.messageBoxValidateFunc,
            parent=self.window(),
        )
        shortCutMessageBox.valueChanged.connect(self._onMessageBoxValueChanged)
        shortCutMessageBox.exec()

    def _onMessageBoxValueChanged(self, value: str):
        """Handle value change from the shortcut dialog.

        :param value: New shortcut value
        :type value: str

        :emits valueChanged: When shortcut value changes
        """
        self.valueChanged.emit(self._configPath, value)
        self.setValue(value)

    def setValue(self, value: str):
        """Set the current shortcut value.

        :param value: Shortcut string (e.g., "Alt+Space")
        :type value: str
        """
        self.shortcut = value
        self.shortcutPicker.setValue(value)
