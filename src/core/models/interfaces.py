from abc import ABC, abstractmethod, ABCMeta
from typing import Any, Union

from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter, Qt
from PySide6.QtGui import QColor, QPainter, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
)
from qfluentwidgets import (
    FluentWindow,
    FluentStyleSheet,
    isDarkTheme,
    IconWidget,
    drawIcon,
    FluentIconBase, setFont,
)


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