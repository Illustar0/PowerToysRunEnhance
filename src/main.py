import sys

import httpx
from PySide6.QtCore import QThread, Signal, QUrl, QSize, QEventLoop, QTimer
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (
    FluentIcon,
    MessageBox,
    Flyout,
    InfoBarIcon,
    FlyoutAnimationType,
    NavigationAvatarWidget,
    SplashScreen,
)
from qfluentwidgets import (
    NavigationItemPosition,
    FluentWindow,
)

from interfaces.main import MainInterface

__VERSION__ = "0.0.1"

from interfaces.setting import SettingInterface


class UpdateCheckerThread(QThread):
    # 定义信号
    update_found = Signal(str, str)  # 发现更新时发送当前版本和最新版本
    update_not_found = Signal()  # 没有更新时发送信号
    check_error = Signal(str)  # 检查出错时发送错误信息

    def run(self):
        try:
            # 使用同步的 httpx 客户端
            response = httpx.get(
                "https://api.github.com/repos/Illustar0/PowerToysRunEnhance/releases/latest"
            )
            response.raise_for_status()
            latest_version = response.json().get("tag_name", "").lstrip("v")

            # 比较版本号
            current_version = __VERSION__

            if latest_version and latest_version != current_version:
                self.update_found.emit(current_version, latest_version)
            else:
                self.update_not_found.emit()
        except Exception as e:
            self.check_error.emit(str(e))


class Window(FluentWindow):
    """主界面"""

    def __init__(self):
        super().__init__()
        self.resize(900, 700)
        self.setWindowIcon(QIcon("./resources/logo.png"))
        self.setWindowTitle("PowerToysRunEnhance")
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))

        # 2. 在创建其他子页面前先显示主界面
        self.show()

        # 延迟 1 秒以显示启动页面
        loop = QEventLoop(self)
        QTimer.singleShot(1000, loop.quit)
        loop.exec()

        self.homeInterface = MainInterface("Main Interface", __VERSION__, self)
        self.settingInterface = SettingInterface("Setting Interface", self)

        # 创建更新检查线程
        self.update_checker = UpdateCheckerThread()
        self.update_checker.update_found.connect(self.on_update_found)
        self.update_checker.update_not_found.connect(self.on_update_not_found)
        self.update_checker.check_error.connect(self.on_check_error)

        self.initNavigation()
        self.splashScreen.finish()
        self.setWindowTitle("PowerToysRunEnhance - Home")
        self.stackedWidget.currentChanged.connect(self.currentWidgetChanged)

    def currentWidgetChanged(self):
        self.currentInterface = self.stackedWidget.currentWidget()
        if self.currentInterface == self.homeInterface:
            self.setWindowTitle("PowerToysRunEnhance - Home")
        elif self.currentInterface == self.settingInterface:
            self.setWindowTitle("PowerToysRunEnhance - Settings")

    def showMessageBox(self):
        w = MessageBox(
            "支持作者🥰",
            "个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀",
            self,
        )
        w.yesButton.setText("Go🥰")
        w.cancelButton.setText("Next time😭")

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://afdian.com/a/Illustar0"))

    def initNavigation(self):
        # 添加子界面到导航
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, "Home")
        self.navigationInterface.addSeparator()

        self.navigationInterface.addWidget(
            routeKey="Avatar",
            widget=NavigationAvatarWidget("Illustar0", "./resources/Avatar.png"),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(
            self.settingInterface,
            FluentIcon.SETTING,
            "Settings",
            NavigationItemPosition.BOTTOM,
        )

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon("./resources/logo.png"))
        self.setWindowTitle("PowerToysRunEnhance")

    def on_update_found(self, current_version, latest_version):
        update_message = MessageBox(
            "检测到更新",
            f"当前版本：{current_version}\n最新版本：{latest_version}",
            self,
        )
        update_message.yesButton.setText("更新")
        update_message.cancelButton.setText("取消")
        if update_message.exec():
            QDesktopServices.openUrl(
                QUrl("https://github.com/Illustar0/PowerToysRunEnhance/releases")
            )

    def on_update_not_found(self):
        Flyout.create(
            icon=InfoBarIcon.SUCCESS,
            title="检查完成",
            content="当前已是最新版本",
            target=self,
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP,
        )

    def on_check_error(self, error_msg):
        MessageBox("检查更新失败", f"错误信息：{error_msg}", self).exec()

    def on_check_update_button_clicked(self) -> None:
        Flyout.create(
            icon=InfoBarIcon.INFORMATION,
            title="检查更新中",
            content="正在检查更新...",
            target=self,
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP,
        )
        # 启动更新检查线程
        self.update_checker.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
