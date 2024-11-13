import os
import pyWinhook as pyHook
import pythoncom
import uiautomation as automation
import comtypes
import threading
from PIL import Image
import pystray
import pyautogui
import toml
import ctypes
from ctypes import wintypes

def is_valid_key(key):
    if key in [chr(i) for i in range(33, 127)] + [chr(i) for i in range(65281, 65375)]:
        return True
    return False

def close_window(hwnd):
    user32.PostMessageW(hwnd, 0x0010, 0, 0)

def activate_window(window_name):
    window = automation.WindowControl(Name=window_name)
    if window.Exists(0, 0):
        window.SetFocus()

class PowerToysRunEnhanceApp:
    def __init__(self):
        self.config = toml.load('config.toml')
        self.searchWindowName = self.config['settings']['searchWindowName']
        self.powerToysRunHotKey = self.config['settings']['powerToysRunHotKey']
        self.autoFocus = self.config['settings']['autoFocus']
        self.enabled = True
        self.stopHook = False

    def on_keyboard_event(self, event):
        if self.stopHook:
            return True
        if event.WindowName== self.searchWindowName and self.enabled:
            if is_valid_key(event.Key):
                self.stopHook = True
                try:
                    comtypes.CoInitialize()
                    close_window(event.Window)
                    pyautogui.hotkey(*self.powerToysRunHotKey.split('+'), interval=0.01)
                    # 一个临时解决方案
                    if self.autoFocus:
                        activate_window("PowerToys.PowerLauncher")
                finally:
                    self.stopHook =False
                    comtypes.CoUninitialize()
            return True
        return True


    def appEnabled(self, icon, item):
        self.enabled = not item.checked

    def quit_app(self, icon, item):
        os._exit(0)

    def create_tray_icon(self):
        image = Image.open("icon.png")
        icon = pystray.Icon("PowerToysRunEnhance", image, menu=pystray.Menu(
            pystray.MenuItem("Enabled", self.appEnabled, checked=lambda item: self.enabled),
            pystray.MenuItem("Quit", self.quit_app)
        ))
        icon.run()

user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

app = PowerToysRunEnhanceApp()
icon_thread = threading.Thread(target=app.create_tray_icon)
icon_thread.start()

hm = pyHook.HookManager()
hm.KeyDown = app.on_keyboard_event
hm.HookKeyboard()

pythoncom.PumpMessages()
