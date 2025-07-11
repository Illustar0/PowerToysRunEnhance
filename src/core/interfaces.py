from abc import ABC, abstractmethod, ABCMeta
from collections import deque
from typing import Protocol, Optional, Any, Union

from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter, Slot, Qt
from PySide6.QtGui import QColor, QPainter, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QSystemTrayIcon,
    QApplication,
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)
from pydantic import BaseModel
from qfluentwidgets import (
    FluentWindow,
    Theme,
    FluentStyleSheet,
    isDarkTheme,
    IconWidget,
    drawIcon,
    FluentIconBase,
)

from src.core.models import CommonConfigModel, AppConfigModel
from src.core.models import InputData


class QWidgetABCMeta(type(QWidget), ABCMeta):
    """Metaclass for QWidget abstract base classes.

    Combines QWidget's metaclass with ABCMeta to enable abstract QWidget classes.
    """

    pass


class FluentIconWidget(IconWidget):
    """Icon widget for setting cards.

    This widget displays icons in setting cards with proper opacity
    handling for disabled states and smooth rendering.
    """

    def paintEvent(self, e):
        """Paint the icon with appropriate styling.

        :param e: Paint event
        :type e: QPaintEvent
        """
        painter = QPainter(self)

        if not self.isEnabled():
            painter.setOpacity(0.36)

        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        drawIcon(self._icon, painter, self.rect())


class FluentCard(QFrame):
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
        self, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None
    ):
        super().__init__(parent=parent)
        self.iconLabel = FluentIconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.contentLabel = QLabel(content or "", self)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        if not content:
            self.contentLabel.hide()

        self.setMinimumHeight(72)
        self.iconLabel.setFixedSize(16, 16)

        # initialize layout
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(16, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.hBoxLayout.addSpacing(16)

        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignLeft)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)

        self.contentLabel.setObjectName("contentLabel")
        FluentStyleSheet.SETTING_CARD.apply(self)

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


class FluentCardABCMeta(type(FluentCard), ABCMeta):
    """Metaclass for QFrame abstract base classes.

    Combines QFrame's metaclass with ABCMeta to enable abstract QFrame classes.
    """

    pass


class QObjectABCMeta(type(QObject), ABCMeta):
    """Metaclass for QObject abstract base classes.

    Combines QObject's metaclass with ABCMeta to enable abstract QObject classes.
    """

    pass


class WindowABCMeta(type(FluentWindow), ABCMeta):
    """Metaclass for FluentWindow abstract base classes.

    Combines FluentWindow's metaclass with ABCMeta to enable abstract FluentWindow classes.
    """

    pass


class QApplicationABCMeta(type(QApplication), ABCMeta):
    """Metaclass for QApplication abstract base classes.

    Combines QApplication's metaclass with ABCMeta to enable abstract QApplication classes.
    """

    pass


class NativeEventFilterABCMeta(type(QAbstractNativeEventFilter), ABCMeta):
    """Metaclass for QAbstractNativeEventFilter abstract base classes.

    Combines QAbstractNativeEventFilter's metaclass with ABCMeta to enable abstract
    native event filter classes.
    """

    pass


class IProviderContext(Protocol):
    """Provider context interface.

    Defines the context and configuration data required by providers to operate.

    :ivar provider_process_name: Name of the provider process
    :type provider_process_name: str
    :ivar provider_path: Optional path to the provider executable
    :type provider_path: Optional[str]
    :ivar provider_hwnd: Optional handle to the provider window
    :type provider_hwnd: Optional[int]
    :ivar common_config: Common configuration model shared across providers
    :type common_config: CommonConfigModel
    :ivar provider_config: Optional provider-specific configuration dictionary
    :type provider_config: Optional[dict]
    :ivar user_input: Optional queue of user input data
    :type user_input: Optional[deque[InputData]]
    """

    provider_process_name: str
    provider_path: Optional[str]
    provider_hwnd: Optional[int]
    common_config: CommonConfigModel
    provider_config: Optional[dict]
    user_input: Optional[deque[InputData]]


class IMainWindow(FluentWindow, ABC, metaclass=WindowABCMeta):
    """Main window interface.

    Defines the interface for the main application window with tray icon support.

    Signals:
        enable_changed (bool): Emitted when the enabled state changes
    """


class INativeEventFilter(
    QAbstractNativeEventFilter, QObject, ABC, metaclass=NativeEventFilterABCMeta
):
    """Native event filter interface.

    Defines the interface for filtering native system events, particularly for theme changes.

    Signals:
        themeChanged (Theme): Emitted when the system theme changes
        themeColorChanged (QColor): Emitted when the theme color changes
    """

    themeChanged = Signal(Theme)
    themeColorChanged = Signal(QColor)


class IProviderSettingGUI(QWidget, ABC, metaclass=QWidgetABCMeta):
    """Provider settings GUI interface.

    Defines the interface for provider-specific settings GUI components.
    """

    pass


class IProvider(QObject, ABC, metaclass=QObjectABCMeta):
    """Provider interface.

    Defines the interface for all providers that handle search operations.

    Signals:
        inputDone: Emitted when input processing is complete
    """

    inputDone = Signal()

    def __init__(self, context: IProviderContext, /):
        """Initialize the provider with context.

        :param context: Provider context containing configuration and state
        :type context: IProviderContext
        """
        super().__init__()
        self.context = context

    @abstractmethod
    def launch(self) -> bool:
        """Launch the provider.

        :returns: True if launch was successful, False otherwise
        :rtype: bool
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up provider resources.

        Should be called when the provider is no longer needed to free resources.
        """
        pass

    @abstractmethod
    def send_input(self) -> None:
        """Send input to the provider.

        Processes and sends user input to the provider for handling.
        """
        pass


class ISettingCard(FluentCard, ABC, metaclass=FluentCardABCMeta):
    """Setting card interface.

    Defines the interface for individual setting card widgets that
    display configuration options with icons, titles, and controls.
    """

    valueChanged = Signal(str, Any)

    @abstractmethod
    def setValue(self, value: Any) -> None:
        """Set the current value of the setting.

        :param value: New value to set
        :type value: Any
        """
        pass

    def addItem(self, *args, **kwargs):
        pass

    def addItems(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def configPath(self) -> str:
        """Get the configuration path for this setting card.

        :returns: Configuration path used to store/retrieve the setting value
        :rtype: str
        """
        pass


class ISettingCardGroup(QWidget, ABC, metaclass=QWidgetABCMeta):
    """Setting card group interface.

    Defines the interface for setting card group widgets that contain
    and manage multiple setting cards with a common theme or category.
    """

    @abstractmethod
    def addSettingCard(self, card: ISettingCard) -> None:
        """Add a single setting card to the group.

        :param card: Setting card to add
        :type card: ISettingCard
        """
        pass

    @abstractmethod
    def addSettingCards(self, cards: list[ISettingCard]) -> None:
        """Add multiple setting cards to the group.

        :param cards: List of setting cards to add
        :type cards: list[ISettingCard]
        """
        pass

    @abstractmethod
    def listSettingCard(self) -> list[ISettingCard]:
        """Get all setting cards in this group.

        :return: List of setting cards
        :rtype: list[ISettingCard]
        """
        pass


class IProviderMeta(Protocol):
    """Provider metadata interface.

    Defines the metadata structure for providers including names, processes, and configuration.

    :ivar provider_name: Unique name identifier for the provider
    :type provider_name: str
    :ivar provider_name_tr: Optional translated name for the provider
    :type provider_name_tr: str | None
    :ivar provider_process_name: List of process names associated with the provider
    :type provider_process_name: list[str]
    :ivar required_config: Optional required configuration string
    :type required_config: Optional[str]
    """

    provider_name: str
    provider_name_tr: str | None = None
    provider_process_name: list[str]
    required_config: Optional[str]
    config_model: type[BaseModel]
    setting_group: Optional[type[ISettingCardGroup]] = None


class IProviderRegistry(ABC):
    """Provider registry interface.

    Defines the interface for managing provider registration and retrieval.
    """

    @abstractmethod
    def register_provider(
        self,
        provider_name: str,
        provider_meta: IProviderMeta,
        provider_class: type[IProvider],
    ) -> None:
        """Register a provider.

        :param provider_name: Unique name for the provider
        :type provider_name: str
        :param provider_meta: Provider metadata
        :type provider_meta: IProviderMeta
        :param provider_class: Provider implementation class
        :type provider_class: type[IProvider]
        :param provider_setting_gui_class: Optional settings GUI class
        :type provider_setting_gui_class: type[IProviderSettingGUI] | None
        """
        pass

    @abstractmethod
    def get_provider_class(self, provider_name: str) -> Optional[type[IProvider]]:
        """Get the provider class by name.

        :param provider_name: Name of the provider
        :type provider_name: str
        :returns: Provider class or None if not found
        :rtype: Optional[type[IProvider]]
        """
        pass

    @abstractmethod
    def get_provider_classes(self) -> dict[str, type[IProvider]]:
        pass

    @abstractmethod
    def get_provider_meta(self, provider_name: str) -> IProviderMeta | None:
        """Get the provider metadata by name.

        :param provider_name: Name of the provider
        :type provider_name: str
        :returns: Provider metadata or None if not found
        :rtype: Optional[IProviderMeta]
        """
        pass

    @abstractmethod
    def get_provider_metas(self) -> dict[str, IProviderMeta]:
        pass

    @abstractmethod
    def get_provider_names(self) -> list[str]:
        """Get all registered provider names.

        :returns: List of provider names
        :rtype: list[str]
        """
        pass


class IProviderFactory(QObject, ABC, metaclass=QObjectABCMeta):
    """Provider factory interface.

    Defines the interface for creating and managing provider instances.

    Signals:
        inputDone: Emitted when input processing is complete
    """

    inputDone = Signal()

    @property
    @abstractmethod
    def provider_instances(self) -> dict[str, IProvider]:
        """Get all provider instances.

        :returns: Dictionary mapping provider names to instances
        :rtype: dict[str, IProvider]
        """
        pass

    @abstractmethod
    def create_instance(
        self, provider_name: str, provider_context: IProviderContext | None = None
    ) -> IProvider:
        """Create a new provider instance.

        :param provider_name: Name of the provider to create
        :type provider_name: str
        :param provider_context: Optional provider context
        :type provider_context: IProviderContext | None
        :returns: Created provider instance
        :rtype: IProvider
        """
        pass

    def get_instance(self, provider_name: str) -> IProvider | None:
        """Get an existing provider instance.

        :param provider_name: Name of the provider
        :type provider_name: str
        :returns: Provider instance or None if not found
        :rtype: IProvider | None
        """
        pass


class IProviderManager(QObject, ABC, metaclass=QObjectABCMeta):
    """Provider manager interface.

    Defines the interface for managing provider lifecycle and operations.

    Signals:
        inputDone: Emitted when input processing is complete
    """

    inputDone = Signal()

    @abstractmethod
    def provider_launch(
        self, provider_name: str, provider_context: IProviderContext
    ) -> bool:
        """Launch a provider.

        :param provider_name: Name of the provider to launch
        :type provider_name: str
        :param provider_context: Provider context
        :type provider_context: IProviderContext
        :returns: True if launch was successful, False otherwise
        :rtype: bool
        """
        pass

    @abstractmethod
    def provider_cleanup(self, provider_name: str) -> None:
        """Clean up a provider.

        :param provider_name: Name of the provider to clean up
        :type provider_name: str
        """
        pass

    @abstractmethod
    def provider_send_input(self, provider_name: str) -> None:
        """Send input to a provider.

        :param provider_name: Name of the provider
        :type provider_name: str
        """
        pass

    @abstractmethod
    def provider_run(self, provider_name: str, method: str):
        """Run a specific method on a provider.

        :param provider_name: Name of the provider
        :type provider_name: str
        :param method: Method name to execute
        :type method: str
        """
        pass


class IKeyboardHook(QObject, ABC, metaclass=QObjectABCMeta):
    """Keyboard hook interface.

    Defines the interface for capturing and handling keyboard events.

    Signals:
        getFocus: Emitted when focus should be obtained
    """

    getFocus = Signal()

    @abstractmethod
    def start_listening(self) -> None:
        """Start listening for keyboard events.

        Begins monitoring keyboard input for configured hotkeys.
        """
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """Stop listening for keyboard events.

        Stops monitoring keyboard input and release resources.
        """
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """Set the enabled state of the keyboard hook.

        :param enabled: Whether the hook should be enabled
        :type enabled: bool
        """
        pass

    @abstractmethod
    def on_windows_search_close(self):
        """Handle Windows search close event.

        Called when the Windows search interface is closed.
        """
        pass

    @abstractmethod
    def on_provider_start_failed(self):
        """Handle provider start failure.

        Called when a provider fails to start properly.
        """
        pass

    @abstractmethod
    def on_provider_started(self, provider_hwnd: int):
        """Handle provider start success.

        :param provider_hwnd: Handle to the provider window
        :type provider_hwnd: int
        """
        pass


class IWindowHook(QObject, ABC, metaclass=QObjectABCMeta):
    """Window hook interface.

    Defines the interface for capturing and handling window events.

    Signals:
        providerStarted: Emitted when a provider starts
        windowsSearchClosed: Emitted when Windows search is closed
        windowsSearchStarted: Emitted when Windows search is started
    """

    providerStarted = Signal()
    windowsSearchClosed = Signal()
    windowsSearchStarted = Signal()

    @abstractmethod
    def set_provider_process_names(self, process_names: list[str]) -> None:
        """Set the provider process names to monitor.

        :param process_names: List of process names to monitor
        :type process_names: list[str]
        """
        pass

    @abstractmethod
    def set_hook(self) -> None:
        """Set up the window hook.

        Installs the window hook to begin monitoring window events.
        """
        pass

    @abstractmethod
    def unset_hook(self) -> None:
        """Remove the window hook.

        Uninstalls the window hook and stops monitoring events.
        """
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """Set the enabled state of the window hook.

        :param enabled: Whether the hook should be enabled
        :type enabled: bool
        """
        pass


class IConfigurationService(QObject, ABC, metaclass=QObjectABCMeta):
    """Configuration service interface.

    Defines the interface for managing application configuration.

    Signals:
        configChanged: Emitted when configuration changes
    """

    configChanged = Signal()

    @property
    @abstractmethod
    def data(self) -> AppConfigModel:
        """Get the configuration data.

        :returns: Current configuration model
        :rtype: AppConfigModel
        """
        pass

    @data.setter
    @abstractmethod
    def data(self, value: AppConfigModel) -> None:
        """Set the configuration data.

        :param value: New configuration model
        :type value: AppConfigModel
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """Save the configuration.

        Persists the current configuration to storage.
        """
        pass

    @abstractmethod
    def load(self) -> None:
        """Load the configuration.

        Loads configuration from storage into memory.
        """
        pass

    @abstractmethod
    def get(self, path: str):
        """Get configuration value using dot notation path.

        :param path: Dot-separated path to the configuration value
        :type path: str

        :return: Configuration value at the specified path
        :rtype: Any

        :raises KeyError: If the configuration path does not exist

        """
        pass

    @abstractmethod
    def set(self, path: str, value: Any):
        """Set the configuration value using dot notation path.

        :param path: Dot-separated path to the configuration value
        :type path: str
        :param value: Value to set at the specified path
        :type value: Any

        :raises KeyError: If the configuration path does not exist

        :emits configChanged: When configuration value is successfully set
        """
        pass


class ITrayIcon(QWidget, ABC, metaclass=QWidgetABCMeta):
    """Tray icon interface.

    Defines the interface for the system tray icon functionality.

    Signals:
        enable_changed (bool): Emitted when enabled state changes
        request_reset_status: Emitted when status reset is requested
        activated (QSystemTrayIcon.ActivationReason): Emitted when tray icon is activated
        run_at_startup_action_triggered (bool): Emitted when run at startup is toggled
    """

    enable_changed = Signal(bool)
    request_reset_status = Signal()
    activated = Signal(QSystemTrayIcon.ActivationReason)
    run_at_startup_action_triggered = Signal(bool)

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """Set the enabled state.

        :param enabled: Whether the tray icon should be enabled
        :type enabled: bool
        """
        pass

    @abstractmethod
    def set_run_at_startup_enabled(self, enabled: bool):
        """Set the run at startup enabled state.

        :param enabled: Whether run at startup should be enabled
        :type enabled: bool
        """
        pass

    @abstractmethod
    def show(self):
        """Show the tray icon.

        Makes the tray icon visible in the system tray.
        """
        pass

    @abstractmethod
    def refresh_enable_icon(self):
        """Refresh the enable icon.

        Forces a refresh of the enable/disable icon state.
        """
        pass


class ITrayIconPresenter(QObject, ABC, metaclass=QObjectABCMeta):
    """Tray icon presenter interface.

    Defines the interface for the tray icon presenter component.

    Signals:
        reset_status: Emitted when status reset is requested
    """

    reset_status = Signal()

    @abstractmethod
    def request_reset_status(self):
        """Request a status reset.

        Triggers a reset of the current status state.
        """
        pass

    @abstractmethod
    def on_theme_changed(self):
        """Handle theme change event.

        Called when the system theme changes.
        """
        pass


class IApplicationModel(QObject, ABC, metaclass=QObjectABCMeta):
    """Application model interface.

    Defines the interface for the main application model.

    Signals:
        enabled_changed (bool): Emitted when enabled state changes
        active_provider_changed (str): Emitted when active provider changes
    """

    enabled_changed = Signal(bool)
    active_provider_changed = Signal(str)

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the application is enabled.

        :returns: True if enabled, False otherwise
        :rtype: bool
        """
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """Set the enabled state.

        :param enabled: Whether the application should be enabled
        :type enabled: bool
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Get the application version.

        :returns: Version string
        :rtype: str
        """
        pass

    @abstractmethod
    def get_active_provider(self) -> str:
        """Get the active provider name.

        :returns: Name of the active provider
        :rtype: str
        """
        pass

    @abstractmethod
    def set_active_provider(self, provider_name: str) -> str:
        """Set the active provider.

        :param provider_name: Name of the provider to activate
        :type provider_name: str
        :returns: Name of the activated provider
        :rtype: str
        """
        pass


class IQApplication(QApplication, ABC, metaclass=QApplicationABCMeta):
    """Application interface.

    Defines the interface for the main QApplication.

    Signals:
        messageReceived (str): Emitted when a message is received
    """

    messageReceived = Signal(str)


class IMainWindowPresenter(QObject, ABC, metaclass=QObjectABCMeta):
    """Main window presenter interface.

    Defines the interface for the main window presenter component.
    """

    @abstractmethod
    def onMessageReceived(self, message: str):
        """Handle received message.

        :param message: The message that was received
        :type message: str
        """
        pass

    @abstractmethod
    def onTrayIconActivated(self, reason: QSystemTrayIcon.ActivationReason):
        pass


class IEventBus(ABC):
    """Event bus interface.

    Defines the interface for event-driven communication between components.
    """

    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to an event type.

        :param event_type: Type of event to subscribe to
        :type event_type: str
        :param handler: Callback function to handle the event
        :type handler: callable
        """
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from an event type.

        :param event_type: Type of event to unsubscribe from
        :type event_type: str
        :param handler: Callback function to remove
        :type handler: callable
        """
        pass

    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event.

        :param event_type: Type of event to publish
        :type event_type: str
        :param data: Optional data to send with the event
        :type data: Any
        """
        pass


class ISettingInterface(QWidget, ABC, metaclass=QWidgetABCMeta):
    """Setting interface abstract base class.

    Defines the interface for setting widgets that contain setting card groups.
    """

    @abstractmethod
    def listSettingCardGroups(self) -> list[ISettingCardGroup]:
        """Get all setting card groups in this interface.

        :return: List of setting card groups
        :rtype: list[ISettingCardGroup]
        """
        pass

    def init_ui(
        self, provider_setting_card_groups_dict: dict[str, type[ISettingCardGroup]]
    ):
        pass


class ISettingInterfacePresenter(QObject, ABC, metaclass=QObjectABCMeta):
    @abstractmethod
    @Slot()
    def onConfigChanged(self):
        pass


class IMainInterfacePresenter(ABC):
    pass


class IMainInterface(QWidget, ABC, metaclass=QWidgetABCMeta):
    """Setting interface abstract base class.

    Defines the interface for setting widgets that contain setting card groups.
    """

    enableChanged = Signal(bool)

    @abstractmethod
    def setEnable(self, enabkled: bool):
        pass

    def init_ui(self, version: str):
        pass
