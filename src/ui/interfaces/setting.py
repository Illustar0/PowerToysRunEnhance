from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QLabel
from qfluentwidgets import SegmentedWidget, PushButton


class SettingInterface(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName(title.replace(" ", "-"))

        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)
        self.MainSettingUI = SettingUI(self)
        # 获取Provider的SettingUI
        # self.ProviderSettingUI=
        self.addSubInterface(self.MainSettingUI, "Main_Setting_UI", "Main")
        # self.addSubInterface(self.ProviderSettingUI, "Provider_Setting_UI", "Provider")

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.MainSettingUI)
        self.pivot.setCurrentItem(self.MainSettingUI.objectName())

        self.vBoxLayout.setContentsMargins(30, 0, 30, 30)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)

        # 使用全局唯一的 objectName 作为路由键
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())


class SettingUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(PushButton(parent=self))
