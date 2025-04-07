import ctypes
import signal
import sys
import time
from ctypes import wintypes
import httpx
import pywinauto
import win32api
import win32con
import win32gui
import win32process
import winput
from PySide6.QtCore import (
    QThread,
    Signal,
    QUrl,
    QSize,
    QEventLoop,
    QTimer,
    Slot,
    QObject,
    QCoreApplication,
    Qt,
)
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from loguru import logger
from pynput import keyboard
from pynput.keyboard import Controller, Key
from qfluentwidgets import (
    FluentIcon,
    MessageBox,
    Flyout,
    InfoBarIcon,
    FlyoutAnimationType,
    NavigationAvatarWidget,
    SplashScreen,
    SystemTrayMenu,
    Action,
)
from qfluentwidgets import (
    NavigationItemPosition,
    FluentWindow,
)

from interfaces.main import MainInterface
from interfaces.setting import (
    SettingInterface,
    CONFIG,
    SPECIAL_KEYS_VKCODE,
    VK_TO_KEY_NAME,
)

__VERSION__ = "0.1.0"


class GlobalSignals(QObject):
    powertoys_launcher_started = Signal(object)
    input_detection_done = Signal(object)
    input_detection_listen = Signal(object)
    SetForegroundWindow = Signal(object)
    enable_status_changed = Signal(bool)


global_signals = GlobalSignals()


class OpenPowertoysRun(QThread):
    def run(self):
        shortcut = CONFIG.get("settings.powerToysRunShortCut", "Alt+Space")
        keyboard = Controller()
        keys = shortcut.split("+")

        # 按下所有键
        for key in keys:
            if key.lower() == "alt":
                keyboard.press(Key.alt)
            elif key.lower() == "ctrl":
                keyboard.press(Key.ctrl)
            elif key.lower() == "shift":
                keyboard.press(Key.shift)
            elif key.lower() == "space":
                keyboard.press(Key.space)
            else:
                keyboard.press(key.lower())

        # 释放所有键
        for key in reversed(keys):
            if key.lower() == "alt":
                keyboard.release(Key.alt)
            elif key.lower() == "ctrl":
                keyboard.release(Key.ctrl)
            elif key.lower() == "shift":
                keyboard.release(Key.shift)
            elif key.lower() == "space":
                keyboard.release(Key.space)
            else:
                keyboard.release(key.lower())


class InputDetectionNext(QThread):
    def __init__(self):
        super().__init__()
        self.powertoys_launcher_window = None
        self.is_listening = False
        self.hwnd = None
        self.buffers = []
        self.listener = keyboard.Listener(win32_event_filter=self.win32_event_filter)
        self.listener.start()
        self.powertoys_launcher_starting = False
        self.query_box = None
        global_signals.powertoys_launcher_started.connect(
            self.powertoys_launcher_started
        )
        global_signals.input_detection_listen.connect(self.listen)

    def get_text_from_buffers(self):
        text = ""
        for keycode in self.buffers:
            if winput.vk_code_dict.get(keycode) == "VK_SPACE":
                text += " "
            else:
                key_name = VK_TO_KEY_NAME.get(winput.vk_code_dict.get(keycode))
                if key_name:
                    text += key_name.lower()
        return text

    def win32_event_filter(self, msg, data):
        if self.is_listening:
            logger.debug(
                f"pynput 捕获到按键{winput.vk_code_dict.get(data.vkCode)},flags={data.flags},msg={msg}"
            )
            if (
                data.vkCode not in SPECIAL_KEYS_VKCODE
                and msg in (256, 257)
                and data.flags in (0, 128)
            ):
                """
                data.flags == 16 表示 LLKHF_INJECTED ，意味着这个输入是模拟键盘事件
                data.flags == 0 则为物理按下键
                """
                process_name = get_process_name(win32gui.GetForegroundWindow())
                if self.powertoys_launcher_starting is not True:
                    if (
                        "SearchHost.exe" not in process_name
                        and "PowerToys.PowerLauncher.exe" not in process_name
                        and process_name != ""
                    ):
                        logger.debug(f"{process_name}非搜索或PowerLauncher，线程休眠")
                        self.sleeping()
                        return

                if msg == 256 and data.flags == 0:
                    self.buffers.append(data.vkCode)
                    if self.powertoys_launcher_starting is False:
                        self.powertoys_launcher_starting = True
                        user32 = ctypes.windll.user32
                        user32.PostMessageW(self.hwnd, 0x0010, 0, 0)
                        time.sleep(0.5)
                        open_powertoys_run = OpenPowertoysRun()
                        open_powertoys_run.run()
                logger.debug(
                    f"按键{winput.vk_code_dict.get(data.vkCode)}被阻止,flags={data.flags},msg={msg}"
                )
                self.listener.suppress_event()

    def run(self):
        return

    def powertoys_launcher_started(self, hwnd):
        logger.debug("powertoys_launcher_started 信号已接收")
        print(self.powertoys_launcher_starting)
        if self.powertoys_launcher_starting:
            if CONFIG.get("settings.autoFocus", True):
                app = pywinauto.Application(backend="uia").connect(handle=hwnd)
                self.powertoys_launcher_window = app.window(handle=hwnd)
                self.query_box = self.powertoys_launcher_window.child_window(
                    auto_id="QueryTextBox"
                )
                if self.query_box.window_text() != "":
                    self.query_box.set_text("")
                global_signals.SetForegroundWindow.emit(hwnd)
                self.query_box.set_focus()
            time.sleep(0.2)
            logger.debug(self.buffers)
            if CONFIG.get("settings.inputMethods", 0) == 0:
                keyboard = Controller()
                for keycode in self.buffers:
                    if winput.vk_code_dict.get(keycode) == "VK_SPACE":
                        keycode = Key.space
                    else:
                        keycode = VK_TO_KEY_NAME.get(
                            winput.vk_code_dict.get(keycode)
                        ).lower()
                    keyboard.type(keycode)
                    time.sleep(0.03)
                    logger.debug(f"尝试输入 {keycode}并设置焦点")
            # 不推荐
            else:
                text = self.get_text_from_buffers()
                if self.query_box is not None:
                    self.query_box.set_text(text)
                else:
                    app = pywinauto.Application(backend="uia").connect(handle=hwnd)
                    self.powertoys_launcher_window = app.window(handle=hwnd)
                    self.query_box = self.powertoys_launcher_window.child_window(
                        auto_id="QueryTextBox"
                    )
                    # self.query_box.set_text(text)
                    self.query_box.type_keys(text)
            self.sleeping()

    def sleeping(self):
        logger.debug("线程进入休眠")
        self.buffers.clear()
        self.is_listening = False
        self.powertoys_launcher_starting = False

    def listen(self, hwnd):
        logger.debug("重新开始监听")
        self.hwnd = hwnd
        self.buffers.clear()
        self.is_listening = True
        self.powertoys_launcher_starting = False


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


def get_process_name(hwnd) -> str:
    """获取窗口所属的进程名"""
    try:
        # 获取进程ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        # 打开进程
        handle = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False,
            pid,
        )
        # 获取进程名
        process_name = win32process.GetModuleFileNameEx(handle, 0)
        win32api.CloseHandle(handle)
        return process_name
    except:
        return ""


class WorkingThread(QThread):
    enable = True
    hook = None
    error = Signal()

    def __init__(self):
        super().__init__()
        self.powertoys_launcher_hwnd = None
        self.inputDetection = InputDetectionNext()
        self.inputDetection.start()
        global_signals.enable_status_changed.connect(self.working)

    @Slot(bool)
    def working(self, checked):
        self.enable = checked
        # 当设置为禁用时，如果线程正在运行，可以考虑重启线程
        if not checked and self.isRunning():
            self.cleanup()
            self.terminate()  # 终止当前线程
            self.wait()  # 等待线程结束
        elif checked and not self.isRunning():
            self.start()  # 如果启用且线程未运行，则启动线程

    # 定义回调函数
    def win_event_callback(
        self,
        hWinEventHook,
        event,
        hwnd,
        idObject,
        idChild,
        dwEventThread,
        dwmsEventTime,
    ):
        # 只有在启用状态下才处理事件
        if not self.enable:
            return

        if event == win32con.EVENT_SYSTEM_FOREGROUND:
            logger.debug(
                f"当前窗口焦点 {win32gui.GetWindowText(hwnd)}:{get_process_name(hwnd)}"
            )
            process_name = get_process_name(hwnd)
            if process_name.find("SearchHost.exe") != -1:
                if CONFIG.get("settings.detectionMethods") == 0:
                    global_signals.input_detection_listen.emit(hwnd)
                    self.powertoys_launcher_hwnd = hwnd

            elif process_name.find("PowerLauncher") != -1:
                print("PowerLauncher")
                global_signals.powertoys_launcher_started.emit(hwnd)

    def input_detection_done(self, data):
        keyboard = Controller()
        for keycode in data:
            if winput.vk_code_dict.get(keycode) == "VK_SPACE":
                keycode = Key.space
            else:
                keycode = VK_TO_KEY_NAME.get(winput.vk_code_dict.get(keycode)).lower()
            print(keycode)
            keyboard.type(keycode)

    def cleanup(self, signal=None, frame=None):
        if self.hook:
            # 取消钩子
            user32 = ctypes.windll.user32
            user32.UnhookWinEvent(self.hook)

    # 注册信号处理
    def run(self):
        # 如果线程启动时处于禁用状态，则直接返回
        if not self.enable:
            return

        WinEventProcType = ctypes.WINFUNCTYPE(
            None,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_long,
            ctypes.c_long,
            ctypes.c_long,
            ctypes.c_long,
            ctypes.c_long,
        )
        # 设置钩子
        callback = WinEventProcType(self.win_event_callback)
        user32 = ctypes.windll.user32

        # 创建事件钩子
        hook = user32.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,  # 监听窗口激活事件
            win32con.EVENT_SYSTEM_FOREGROUND,
            0,
            callback,
            0,
            0,
            win32con.WINEVENT_OUTOFCONTEXT,
        )

        if hook == 0:
            self.error.emit()
            self.cleanup()
            self.terminate()  # 终止当前线程
            self.wait()  # 等待线程结束

        # 消息循环
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0 and self.enable:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setIcon(parent.windowIcon())


class Window(FluentWindow):
    """主界面"""

    def __init__(self):
        super().__init__()
        self.resize(900, 700)
        self.setWindowIcon(QIcon("./resources/logo.png"))
        self.setWindowTitle("PowerToysRunEnhance")
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
        global_signals.enable_status_changed.connect(self.enable_status)

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

        self.mainWork = WorkingThread()
        self.mainWork.start()
        self.mainWork.error.connect(self.on_main_working_thread_error)
        self.homeInterface.enableCard.enable.connect(self.mainWork.working)

        # 程序关闭时清理 Hook
        signal.signal(signal.SIGINT, self.mainWork.cleanup)
        signal.signal(signal.SIGTERM, self.mainWork.cleanup)

        self.initNavigation()
        self.splashScreen.finish()
        self.setWindowTitle("PowerToysRunEnhance - Home")
        self.stackedWidget.currentChanged.connect(self.currentWidgetChanged)
        self.setup_system_tray()

    @Slot(bool)
    def enable_status(self, checked):
        logger.debug(checked)
        self.homeInterface.enableCard.switchButton.setChecked(checked)

    def setup_system_tray(self):
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(
            QIcon("./resources/logo.png")
        )  # 设置图标，需替换为你自己的图标路径
        self.tray_icon.setToolTip("PowerToysRunEnhance")

        # 创建托盘菜单
        self.menu = SystemTrayMenu(parent=self)
        self.enableAction = Action(
            "✓ 启用",
            checkable=True,
            checked=True,
            triggered=self.on_enable_checkbox_changed,
        )
        self.menu.addActions(
            [
                self.enableAction,
                Action("     显示主界面", triggered=self.show_window),
            ]
        )
        self.menu.addSeparator()
        self.menu.addActions(
            [
                Action("     退出", triggered=QApplication.quit),
            ]
        )

        self.tray_icon.setContextMenu(self.menu)

        # 连接托盘图标的激活信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # 显示托盘图标
        self.tray_icon.show()

    def on_enable_checkbox_changed(self):
        if self.enableAction.isChecked():
            self.enableAction.setText("✓ 启用")
            global_signals.enable_status_changed.emit(True)
        else:
            self.enableAction.setText("✗ 启用")
            global_signals.enable_status_changed.emit(False)

    @Slot(QSystemTrayIcon.ActivationReason)
    def on_tray_icon_activated(self, reason):
        # 当双击托盘图标时
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        # 显示并激活窗口
        self.show()
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized
            | Qt.WindowState.WindowActive
        )
        self.activateWindow()

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

    def on_main_working_thread_error(self):
        self.homeInterface.enableCard.switchButton.setChecked(False)
        errorMessageBox = MessageBox(
            "Hook 注册失败",
            "Hook 注册失败",
            self,
        )
        errorMessageBox.yesButton.setText("哦")
        errorMessageBox.cancelButton.setText("哦")
        errorMessageBox.exec()

    def closeEvent(self, event):
        # 忽略退出事件，而是隐藏到托盘
        event.ignore()
        self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
