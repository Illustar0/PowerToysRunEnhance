import uiautomation as automation
import comtypes
import os
import string
from pynput import keyboard
import pyautogui

alphabet = list(string.ascii_lowercase)


def on_press(key):
    try:
        if key.char.lower() in alphabet:
            comtypes.CoInitialize()
            window = automation.WindowControl(Name="搜索", className="Windows.UI.Core.CoreWindow", searchDepth=2)
            if window.Exists(0, 0):
                RichEditBox = window.EditControl(AutomationId="SearchTextBox", className="RichEditBox")
                ValuePattern = RichEditBox.GetPattern(automation.PatternId.ValuePattern)
                if ValuePattern is None:
                    value = ''
                else:
                    value = ValuePattern.Value
                os.kill(window.ProcessId, 9)
                pyautogui.hotkey("alt", "space")
                pyautogui.typewrite(value)

            comtypes.CoUninitialize()
    except AttributeError:
        pass


with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
