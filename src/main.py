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
from PySide6 import QtCore
from PySide6.QtCore import (
    QThread,
    Signal,
    QUrl,
    QSize,
    QEventLoop,
    QTimer,
    Slot,
    QObject,
    Qt,
    QLocale,
    QSharedMemory,
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
    Dialog,
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
    setting_event_bus,
)
from language import TranslatorManager, LANGUAGE_MAP

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
            elif key.lower() == "win":
                keyboard.press(Key.cmd)
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
            elif key.lower() == "win":
                keyboard.release(Key.cmd)
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
                and msg in (256, 257, 260, 261)
                and (data.flags & 0x10) == 0
            ):
                """
                data.flags == 16 表示 LLKHF_INJECTED ，意味着这个输入是模拟键盘事件
                data.flags == 0 则为物理按下键
                """
                process_name = get_process_name(win32gui.GetForegroundWindow())
                if self.powertoys_launcher_starting is not True:
                    if (
                        "SearchHost.exe" not in process_name
                        and "SearchUI.exe" not in process_name
                        and "SearchApp.exe" not in process_name
                        and "Microsoft.CmdPal.UI.exe" not in process_name
                        and "PowerToys.PowerLauncher.exe" not in process_name
                        and process_name != ""
                    ):
                        logger.debug(f"{process_name}非搜索或PowerLauncher，线程休眠")
                        self.sleeping()
                        return

                if msg in (257, 261):
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
        """
        # 当设置为禁用时，如果线程正在运行，可以考虑重启线程
        if not checked and self.isRunning():
            self.cleanup()
            self.terminate()  # 终止当前线程
            self.wait()  # 等待线程结束
        elif checked and not self.isRunning():
            self.start()  # 如果启用且线程未运行，则启动线程
        """

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
            if (
                process_name.find("SearchHost.exe") != -1
                or process_name.find("SearchUI.exe") != -1
                or process_name.find("SearchApp.exe") != -1
            ):
                if CONFIG.get("settings.detectionMethods") == 0:
                    global_signals.input_detection_listen.emit(hwnd)
                    self.powertoys_launcher_hwnd = hwnd

            elif (
                    process_name.find("PowerToys.PowerLauncher.exe") != -1
                    or process_name.find("Microsoft.CmdPal.UI.exe") != -1
            ):
                global_signals.powertoys_launcher_started.emit(hwnd)

    def input_detection_done(self, data):
        keyboard = Controller()
        for keycode in data:
            if winput.vk_code_dict.get(keycode) == "VK_SPACE":
                keycode = Key.space
            else:
                keycode = VK_TO_KEY_NAME.get(winput.vk_code_dict.get(keycode)).lower()
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
        setting_event_bus.language_changed.connect(self.change_language)

        # 2. 在创建其他子页面前先显示主界面
        self.show()

        # 延迟 1 秒以显示启动页面
        loop = QEventLoop(self)
        QTimer.singleShot(1000, loop.quit)
        loop.exec()

        self.homeInterface = MainInterface("Main Interface", __VERSION__, self)

        self.settingInterface = SettingInterface("Setting Interface", self)
        if TranslatorManager.instance().get_current_language() is not None:
            self.settingInterface.languageCard.comboBox.setCurrentText(
                LANGUAGE_MAP[TranslatorManager.instance().get_current_language()]
            )
        else:
            self.settingInterface.languageCard.comboBox.setCurrentText("English")
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
            self.tr("✓ Enable"),  # "✓ 启用"
            checkable=True,
            checked=True,
            triggered=self.on_enable_checkbox_changed,
        )
        self.menu.addActions(
            [
                self.enableAction,
                Action(
                    self.tr("     Show Main Window"),  # "     显示主界面"
                    triggered=self.show_window,
                ),
            ]
        )
        self.menu.addSeparator()
        self.menu.addActions(
            [
                Action(
                    self.tr("     Exit"),  # "     退出"
                    triggered=self.quit_application,
                ),
            ]
        )

        self.tray_icon.setContextMenu(self.menu)

        # 连接托盘图标的激活信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # 显示托盘图标
        self.tray_icon.show()

    def on_enable_checkbox_changed(self):
        if self.enableAction.isChecked():
            self.enableAction.setText(self.tr("✓ Enable"))  # "✓ 启用"
            global_signals.enable_status_changed.emit(True)
        else:
            self.enableAction.setText(self.tr("✗ Enable"))  # "✗ 启用"
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
            self.tr("Support the Author🥰"),  # "支持作者🥰"
            self.tr(
                "Personal development is not easy. If this project has helped you, please consider buying the author a bottle of happy water🥤. Your support is the motivation for the author to develop and maintain the project🚀"  # "个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀"
            ),
            self,
        )
        w.yesButton.setText(self.tr("Go🥰"))  # "Go🥰"
        w.cancelButton.setText(self.tr("Maybe Next Time😭"))  # "下次一定😭"

        if w.exec():
            QDesktopServices.openUrl(
                QUrl(self.tr("https://ko-fi.com/illustar0"))
            )  # "https://afdian.com/a/Illustar0"

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
            self.tr("Update Detected"),  # "检测到更新"
            self.tr(
                "Current Version: {current_version}\nLatest Version: {latest_version}"
            ).format(
                current_version=current_version, latest_version=latest_version
            ),  # "当前版本：{current_version}\n最新版本：{latest_version}"
            self,
        )
        update_message.yesButton.setText(self.tr("Update"))  # "更新"
        update_message.cancelButton.setText(self.tr("Cancel"))  # "取消"
        if update_message.exec():
            QDesktopServices.openUrl(
                QUrl("https://github.com/Illustar0/PowerToysRunEnhance/releases")
            )

    def on_update_not_found(self):
        Flyout.create(
            icon=InfoBarIcon.SUCCESS,
            title=self.tr("Check Complete"),  # "检查完成"
            content=self.tr("You are using the latest version"),  # "当前已是最新版本"
            target=self,
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP,
        )

    def on_check_error(self, error_msg):
        messagebox = MessageBox(
            self.tr("Update Check Failed"),  # "检查更新失败"
            self.tr("Error Message: {error_msg}").format(
                error_msg=error_msg
            ),  # f"错误信息：{error_msg}"
            self,
        )
        messagebox.yesButton.setText(self.tr("OK"))  # "确定"
        messagebox.cancelButton.hide()
        messagebox.exec()

    def on_check_update_button_clicked(self) -> None:
        Flyout.create(
            icon=InfoBarIcon.INFORMATION,
            title=self.tr("Checking for Updates"),  # "检查更新中"
            content=self.tr("Checking for updates..."),  # "正在检查更新..."
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
            self.tr("Hook Failed"),  # "Hook 失败"
            self.tr("Hook failed, the program will exit"),  # "Hook 失败，程序将退出"
            self,
        )
        errorMessageBox.yesButton.setText(self.tr("OK"))  # "确定"
        errorMessageBox.cancelButton.hide()
        errorMessageBox.exec()
        # 设置退出码为1并结束事件循环
        QApplication.exit(1)

    def closeEvent(self, event):
        # 忽略退出事件，而是隐藏到托盘
        event.ignore()
        self.hide()

    def change_language(self, language):
        translator_manager = TranslatorManager.instance()
        # translator_manager.switch_translator(language)
        messagebox = MessageBox(
            self.tr("Restart Application"),  # "重启应用"
            self.tr(
                "Switching language requires restarting the application. Do you want to continue?"
            ),  # "切换语言需要重启应用，是否继续？"
            self,
        )
        messagebox.yesButton.setText(self.tr("OK"))  # "确定"
        messagebox.cancelButton.setText(self.tr("Cancel"))  # "取消"
        if messagebox.exec():
            translator_manager.switch_translator(language)
            # 在重启前先隐藏并移除托盘图标
            if hasattr(self, "tray_icon") and self.tray_icon is not None:
                self.tray_icon.hide()
                self.tray_icon.setParent(None)
            process = QtCore.QProcess()
            process.startDetached(sys.executable, sys.argv)
            QApplication.quit()

    def quit_application(self):
        # 在退出前先隐藏并移除托盘图标
        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            self.tray_icon.hide()
            self.tray_icon.setParent(None)
            self.tray_icon.deleteLater()
            # del self.tray_icon
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # 在创建主窗口之前检查共享内存
    shared_mem = QSharedMemory("PowerToysRunEnhance")

    translator_manager = TranslatorManager.instance()
    translator_load_failed = None
    if CONFIG.get("settings.language") is None:
        print(QLocale.system().name())
        if translator_manager.switch_translator(QLocale.system().name()) is False:
            if translator_manager.switch_translator("en_US") is False:
                translator_load_failed = True
    else:
        if (
            translator_manager.switch_translator(CONFIG.get("settings.language"))
            is False
        ):
            translator_load_failed = True
    if translator_load_failed is None:
        CONFIG.set("settings.language", translator_manager.get_current_language())
    else:
        CONFIG.set("settings.language", "en_US")
    if translator_load_failed:
        messagebox = Dialog(
            "Translation file loading failed",
            "The system will revert to the default language, English. Please check if the program is complete.",
            None,
        )
        messagebox.yesButton.setText("OK")
        messagebox.cancelButton.hide()
        messagebox.exec()
    # 尝试附加到现有共享内存（检查是否已运行）
    if shared_mem.attach():
        messagebox = Dialog(
            QApplication.translate("__main__", "Error"),
            QApplication.translate("__main__", "The application is already running!"),
            None,
        )
        messagebox.yesButton.setText("OK")
        messagebox.cancelButton.hide()
        messagebox.exec()

        # 清理共享内存
        shared_mem.detach()
        sys.exit(1)

    # 创建共享内存
    if not shared_mem.create(1):
        messagebox = Dialog(
            QApplication.translate("__main__", "Error"),
            QApplication.translate("__main__", "Unable to create shared memory!"),
            None,
        )
        messagebox.yesButton.setText("OK")
        messagebox.cancelButton.hide()
        messagebox.exec()

        if shared_mem.isAttached():
            shared_mem.detach()
        sys.exit(1)
    # 创建主窗口
    w = Window()
    w.show()
    exit_code = app.exec()

    # 程序结束时清理共享内存
    if shared_mem.isAttached():
        shared_mem.detach()

    sys.exit(exit_code)
