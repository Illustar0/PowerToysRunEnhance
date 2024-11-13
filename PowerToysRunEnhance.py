import pystray
import uiautomation as automation
import comtypes
import os
import threading
from PIL import Image
from pynput import keyboard
import pyautogui
import toml

global Enabled
config = toml.load('config.toml')
searchWindowName = config['settings']['searchWindowName']
powerToysRunHotKey = config['settings']['powerToysRunHotKey']


def on_press(key):
    global Enabled
    if Enabled:
        try:
            if hasattr(key, 'char') and key.char is not None:
                comtypes.CoInitialize()
                window = automation.WindowControl(Name=searchWindowName, className="Windows.UI.Core.CoreWindow",
                                                  searchDepth=2)
                if window.Exists(0, 0):
                    RichEditBox = window.EditControl(AutomationId="SearchTextBox", className="RichEditBox")
                    ValuePattern = RichEditBox.GetPattern(automation.PatternId.ValuePattern)
                    if ValuePattern is None:
                        value = ''
                    else:
                        value = ValuePattern.Value
                    os.kill(window.ProcessId, 9)
                    pyautogui.hotkey(*powerToysRunHotKey.split('+'))
                    pyautogui.typewrite(value)

                comtypes.CoUninitialize()
        except AttributeError:
            pass


def appEnabled(icon, item):
    global Enabled
    Enabled = not item.checked


def quit_app(icon, item):
    icon.stop()
    quit()


def create_tray_icon():
    global Enabled
    Enabled = True
    image = Image.open("icon.png")
    icon = pystray.Icon("PowerToysRunEnhance", image, menu=pystray.Menu(
        pystray.MenuItem("Enabled", appEnabled, checked=lambda item: Enabled),
        pystray.MenuItem("Quit", quit_app)
    ))
    icon.run()


icon_thread = threading.Thread(target=create_tray_icon)
icon_thread.start()

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
