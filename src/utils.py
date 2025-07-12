import ctypes
import sys
import winreg
from abc import ABC, abstractmethod, ABCMeta
from os import PathLike
from pathlib import Path

import psutil
import win32api
import win32con
import win32process
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from loguru import logger

# 感谢 Gemini
VK_CODE_SPECIAL_MAP = {
    # --------------------------------------------------------------------------
    # 鼠标按键 (Mouse Buttons)
    # --------------------------------------------------------------------------
    1: "Left Mouse Button",  # VK_LBUTTON, 鼠标左键
    2: "Right Mouse Button",  # VK_RBUTTON, 鼠标右键
    3: "Control-break",  # VK_CANCEL, Cancel 键 (Ctrl+Break)
    4: "Middle Mouse Button",  # VK_MBUTTON, 鼠标中键
    5: "X1 Mouse Button",  # VK_XBUTTON1, 鼠标侧键1 (通常是“后退”)
    6: "X2 Mouse Button",  # VK_XBUTTON2, 鼠标侧键2 (通常是“前进”)
    # --------------------------------------------------------------------------
    # 控制与基本功能键 (Control & Basic Function Keys)
    # --------------------------------------------------------------------------
    8: "Backspace",  # VK_BACK, 退格键
    9: "Tab",  # VK_TAB, Tab 键
    12: "Clear",  # VK_CLEAR, Clear 键 (小键盘5在NumLock关闭时)
    13: "Enter",  # VK_RETURN, 回车键
    16: "Shift",  # VK_SHIFT, Shift 键 (通用, 不区分左右)
    17: "Ctrl",  # VK_CONTROL, Ctrl 键 (通用, 不区分左右)
    18: "Alt",  # VK_MENU, Alt 键 (通用, 不区分左右)
    19: "Pause",  # VK_PAUSE, Pause/Break 键
    20: "Caps Lock",  # VK_CAPITAL, 大写锁定键
    # --------------------------------------------------------------------------
    # IME (输入法) 相关键
    # --------------------------------------------------------------------------
    21: "IME Kana/Hangul mode",  # VK_KANA / VK_HANGUL
    23: "IME Junja mode",  # VK_JUNJA
    24: "IME final mode",  # VK_FINAL
    25: "IME Hanja/Kanji mode",  # VK_HANJA / VK_KANJI
    # --------------------------------------------------------------------------
    # 其他功能键 (Other Function Keys)
    # --------------------------------------------------------------------------
    27: "Esc",  # VK_ESCAPE, Escape 键
    28: "IME convert",  # VK_CONVERT, (输入法) 转换
    29: "IME nonconvert",  # VK_NONCONVERT, (输入法) 非转换
    30: "IME accept",  # VK_ACCEPT, (输入法) 接受
    31: "IME mode change",  # VK_MODECHANGE, (输入法) 模式更改
    # --------------------------------------------------------------------------
    # 空格与导航键 (Space & Navigation Keys)
    # --------------------------------------------------------------------------
    32: "Space",  # VK_SPACE, 空格键
    33: "Page Up",  # VK_PRIOR, Page Up 键
    34: "Page Down",  # VK_NEXT, Page Down 键
    35: "End",  # VK_END, End 键
    36: "Home",  # VK_HOME, Home 键
    37: "Left Arrow",  # VK_LEFT, 左箭头
    38: "Up Arrow",  # VK_UP, 上箭头
    39: "Right Arrow",  # VK_RIGHT, 右箭头
    40: "Down Arrow",  # VK_DOWN, 下箭头
    41: "Select",  # VK_SELECT, Select 键
    42: "Print",  # VK_PRINT, Print 键
    43: "Execute",  # VK_EXECUTE, Execute 键
    44: "Print Screen",  # VK_SNAPSHOT, Print Screen 键
    45: "Insert",  # VK_INSERT, Insert 键
    46: "Delete",  # VK_DELETE, Delete 键
    47: "Help",  # VK_HELP, Help 键
    # --------------------------------------------------------------------------
    # 系统相关键 (System Keys)
    # --------------------------------------------------------------------------
    91: "Win",  # VK_LWIN, 左 Win 键
    92: "Win",  # VK_RWIN, 右 Win 键
    93: "Apps",  # VK_APPS, 应用程序/菜单键
    95: "Sleep",  # VK_SLEEP, 睡眠键
    # --------------------------------------------------------------------------
    # 数字小键盘 (Numeric Keypad)
    # --------------------------------------------------------------------------
    96: "Numpad 0",  # VK_NUMPAD0, 小键盘 0
    97: "Numpad 1",  # VK_NUMPAD1, 小键盘 1
    98: "Numpad 2",  # VK_NUMPAD2, 小键盘 2
    99: "Numpad 3",  # VK_NUMPAD3, 小键盘 3
    100: "Numpad 4",  # VK_NUMPAD4, 小键盘 4
    101: "Numpad 5",  # VK_NUMPAD5, 小键盘 5
    102: "Numpad 6",  # VK_NUMPAD6, 小键盘 6
    103: "Numpad 7",  # VK_NUMPAD7, 小键盘 7
    104: "Numpad 8",  # VK_NUMPAD8, 小键盘 8
    105: "Numpad 9",  # VK_NUMPAD9, 小键盘 9
    106: "Multiply",  # VK_MULTIPLY, 小键盘乘号 (*)
    107: "Add",  # VK_ADD, 小键盘加号 (+)
    108: "Separator",  # VK_SEPARATOR, 小键盘分隔符
    109: "Subtract",  # VK_SUBTRACT, 小键盘减号 (-)
    110: "Decimal",  # VK_DECIMAL, 小键盘小数点 (.)
    111: "Divide",  # VK_DIVIDE, 小键盘除号 (/)
    # --------------------------------------------------------------------------
    # 功能键 F1-F24 (Function Keys)
    # --------------------------------------------------------------------------
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    124: "F13",
    125: "F14",
    126: "F15",
    127: "F16",
    128: "F17",
    129: "F18",
    130: "F19",
    131: "F20",
    132: "F21",
    133: "F22",
    134: "F23",
    135: "F24",
    # --------------------------------------------------------------------------
    # 状态锁定键 (State Lock Keys)
    # --------------------------------------------------------------------------
    144: "Num Lock",  # VK_NUMLOCK, 数字锁定键
    145: "Scroll Lock",  # VK_SCROLL, 滚动锁定键
    # --------------------------------------------------------------------------
    # 特定的左/右修饰键 (Left/Right Specific Modifier Keys)
    # --------------------------------------------------------------------------
    160: "Shift",  # VK_LSHIFT, 左 Shift 键
    161: "Shift",  # VK_RSHIFT, 右 Shift 键
    162: "Ctrl",  # VK_LCONTROL, 左 Ctrl 键
    163: "Ctrl",  # VK_RCONTROL, 右 Ctrl 键
    164: "Alt",  # VK_LMENU, 左 Alt 键
    165: "Alt",  # VK_RMENU, 右 Alt 键 (或 AltGr)
    # --------------------------------------------------------------------------
    # 浏览器与多媒体键 (Browser & Media Keys)
    # --------------------------------------------------------------------------
    166: "Browser Back",  # VK_BROWSER_BACK, 浏览器后退
    167: "Browser Forward",  # VK_BROWSER_FORWARD, 浏览器前进
    168: "Browser Refresh",  # VK_BROWSER_REFRESH, 浏览器刷新
    169: "Browser Stop",  # VK_BROWSER_STOP, 浏览器停止
    170: "Browser Search",  # VK_BROWSER_SEARCH, 浏览器搜索
    171: "Browser Favorites",  # VK_BROWSER_FAVORITES, 浏览器收藏
    172: "Browser Home",  # VK_BROWSER_HOME, 浏览器主页
    173: "Volume Mute",  # VK_VOLUME_MUTE, 静音
    174: "Volume Down",  # VK_VOLUME_DOWN, 音量减
    175: "Volume Up",  # VK_VOLUME_UP, 音量加
    176: "Next Track",  # VK_MEDIA_NEXT_TRACK, 下一曲
    177: "Prev Track",  # VK_MEDIA_PREV_TRACK, 上一曲
    178: "Stop Media",  # VK_MEDIA_STOP, 停止播放
    179: "Play/Pause Media",  # VK_MEDIA_PLAY_PAUSE, 播放/暂停
    # --------------------------------------------------------------------------
    # 应用程序启动键 (Application Launch Keys)
    # --------------------------------------------------------------------------
    180: "Start Mail",  # VK_LAUNCH_MAIL, 启动邮件
    181: "Select Media",  # VK_LAUNCH_MEDIA_SELECT, 选择媒体
    182: "Start App 1",  # VK_LAUNCH_APP1, 启动应用1
    183: "Start App 2",  # VK_LAUNCH_APP2, 启动应用2
    # --------------------------------------------------------------------------
    # 其他特殊/系统键
    # --------------------------------------------------------------------------
    229: "Process Key",  # VK_PROCESSKEY, (输入法) 处理键
    231: "Packet",  # VK_PACKET, 用于传递 Unicode 字符
    246: "Attn",  # VK_ATTN, Attn 键
    247: "CrSel",  # VK_CRSEL, CrSel 键
    248: "ExSel",  # VK_EXSEL, ExSel 键
    249: "Erase EOF",  # VK_EREOF, Erase EOF 键
    250: "Play",  # VK_PLAY, Play 键
    251: "Zoom",  # VK_ZOOM, Zoom 键
    254: "PA1",  # VK_PA1, PA1 键
}


def get_process_path(hwnd) -> str:
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


# So Microsoft, fuck you!
class QWidgetABCMeta(type(QWidget), ABCMeta):
    """Metaclass for QWidget abstract base classes.

    Combines QWidget's metaclass with ABCMeta to enable abstract QWidget classes.
    """

    pass


class IAggressiveDialog(QWidget, ABC, metaclass=QWidgetABCMeta):
    """Aggressive dialog interface.

    Defines the interface for dialogs that aggressively capture focus.
    """

    @abstractmethod
    def get_focus(self):
        """Get focus for the dialog.

        Forces the dialog to capture and maintain focus.
        """
        pass


class AggressiveDialog(IAggressiveDialog):
    """用于抢占焦点的 QWidget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowOpacity(0)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.Tool
        )

    def get_focus(self):
        self.show()
        force_set_foreground_window(self.winId())


def force_set_foreground_window(hwnd: int):
    """使用 AttachThreadInput 来强制将窗口设为前台"""
    user32 = ctypes.windll.user32

    foreground_thread_id = user32.GetWindowThreadProcessId(
        user32.GetForegroundWindow(), None
    )
    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

    user32.AttachThreadInput(foreground_thread_id, current_thread_id, True)

    try:
        user32.BringWindowToTop(hwnd)
        user32.ShowWindow(hwnd, 5)
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)
    finally:
        user32.AttachThreadInput(foreground_thread_id, current_thread_id, False)


def get_app_current_theme():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        0,
        winreg.KEY_READ,
    ) as key:
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    if value == 1:
        return "light"
    else:
        return "dark"


def touch_run_at_startup():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_ALL_ACCESS,
    ) as key:
        try:
            value, _ = winreg.QueryValueEx(key, "WindowsSearchUtility")
            if value != sys.executable:
                winreg.SetValueEx(
                    key, "WindowsSearchUtility", 0, winreg.REG_SZ, sys.executable
                )
        except FileNotFoundError:
            winreg.SetValueEx(
                key, "WindowsSearchUtility", 0, winreg.REG_SZ, sys.executable
            )
        except Exception as e:
            logger.error(f"Error occurred when trying touch run at startup: {e}")


def get_run_at_startup() -> bool:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_READ,
    ) as key:
        try:
            value, _ = winreg.QueryValueEx(key, "WindowsSearchUtility")
            if value != sys.executable:
                return False
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error occurred when trying get run at startup: {e}")
            return False


def get_base_path() -> Path:
    if "__compiled__" in globals():
        return Path(sys.executable).parent
    else:
        return Path(sys.path[0])


def enable_run_at_startup():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_WRITE,
    ) as key:
        winreg.SetValueEx(key, "WindowsSearchUtility", 0, winreg.REG_SZ, sys.executable)


def disable_run_at_startup():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_WRITE,
    ) as key:
        try:
            winreg.DeleteValue(key, "WindowsSearchUtility")
        except FileNotFoundError:
            logger.error("Key not found.")
        except Exception as e:
            logger.error(f"Error occurred when trying disable run at startup: {e}")


def find_processes_by_name(target_names: list | set) -> bool:
    """
    查找进程
    """
    target_set = set(target_names)

    for process in psutil.process_iter(["name"]):
        try:
            process_name = process.info["name"]
            if process_name in target_set:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def vk_code_to_char(
    vk_code: int, shift: bool = False, ctrl: bool = False, alt: bool = False
):
    """
    将 VK_CODE 转换为对应的字符

    :param vk_code: 虚拟键码
    :param shift: 是否按下Shift键
    :param ctrl: 是否按下Ctrl键
    :param alt: 是否按下Alt键
    :return: 对应的字符，如果无法转换则返回None
    """
    user32 = ctypes.windll.user32

    # 获取当前键盘布局
    hkl = user32.GetKeyboardLayout(0)

    # 构建键盘状态数组
    keyboard_state = (ctypes.c_ubyte * 256)()

    # 设置修饰键状态
    if shift:
        keyboard_state[0x10] = 0x80  # VK_SHIFT
    if ctrl:
        keyboard_state[0x11] = 0x80  # VK_CONTROL
    if alt:
        keyboard_state[0x12] = 0x80  # VK_MENU (Alt)

    # 获取扫描码
    scan_code = user32.MapVirtualKeyExW(vk_code, 0, hkl)

    # 转换为Unicode字符
    buffer = ctypes.create_unicode_buffer(10)
    result = user32.ToUnicodeEx(
        vk_code,  # 虚拟键码
        scan_code,  # 扫描码
        keyboard_state,  # 键盘状态
        buffer,  # 输出缓冲区
        len(buffer),  # 缓冲区大小
        0,  # 标志
        hkl,  # 键盘布局句柄
    )

    if VK_CODE_SPECIAL_MAP.get(vk_code) is not None:
        return VK_CODE_SPECIAL_MAP.get(vk_code)
    elif result > 0:
        return buffer.value[:result]
    else:
        return None


def register_aumid(aumid: str, app_name: str, icon_path: str | PathLike | Path):
    if icon_path is not None:
        icon_path = Path(icon_path)
        if not icon_path.exists():
            raise ValueError(
                f"Could not register the application: File {icon_path} does not exist"
            )
        elif icon_path.suffix != ".ico":
            raise ValueError(
                f"Could not register the application: File {icon_path} must be of type .ico"
            )

    winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    keyPath = f"SOFTWARE\\Classes\\AppUserModelId\\{aumid}"
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, keyPath) as masterKey:
        winreg.SetValueEx(masterKey, "DisplayName", 0, winreg.REG_SZ, app_name)
        if icon_path is not None:
            winreg.SetValueEx(
                masterKey, "IconUri", 0, winreg.REG_SZ, str(icon_path.resolve())
            )
