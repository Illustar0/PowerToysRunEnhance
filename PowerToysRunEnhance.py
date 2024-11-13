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
import tkinter as tk
from tkinter import messagebox
import webbrowser
import re


def is_valid_key(key):
    if key in [chr(i) for i in range(33, 127)] + [chr(i) for i in range(65281, 65375)]:
        return True
    return False


def close_window(hwnd):
    user32.PostMessageW(hwnd, 0x0010, 0, 0)


def highlight_toml(text_widget):
    # 清除所有现有标签
    text_widget.tag_remove("key", "1.0", tk.END)
    text_widget.tag_remove("string", "1.0", tk.END)
    text_widget.tag_remove("comment", "1.0", tk.END)

    toml_key_pattern = r'^\s*([\w\-]+)\s*='
    toml_string_pattern = r'\"(.*?)\"'
    toml_comment_pattern = r'#.*$'

    content = text_widget.get("1.0", tk.END)

    for match in re.finditer(toml_key_pattern, content, re.MULTILINE):
        start, end = match.span(1)
        start_index = f"1.0 + {start} chars"
        end_index = f"1.0 + {end} chars"
        text_widget.tag_add("key", start_index, end_index)

    for match in re.finditer(toml_string_pattern, content):
        start, end = match.span()
        start_index = f"1.0 + {start} chars"
        end_index = f"1.0 + {end} chars"
        text_widget.tag_add("string", start_index, end_index)

    for match in re.finditer(toml_comment_pattern, content):
        start, end = match.span()
        start_index = f"1.0 + {start} chars"
        end_index = f"1.0 + {end} chars"
        text_widget.tag_add("comment", start_index, end_index)


def activate_window(window_name):
    window = automation.WindowControl(Name=window_name)
    if window.Exists(0, 0):
        window.SetFocus()


class PowerToysRunEnhanceApp:
    def __init__(self):
        try:
            self.config = toml.load('config.toml')
        except Exception as e:
            self.show_config_error_dialog(e)
        self.searchWindowName = self.config['settings']['searchWindowName']
        self.powerToysRunHotKey = self.config['settings']['powerToysRunHotKey']
        self.autoFocus = self.config['settings']['autoFocus']
        self.enabled = True
        self.stopHook = False

    def show_config_error_dialog(self, error):
        def run_dialog():
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Unable to load config", f"Unable to load config.toml: {str(error)}")
            root.destroy()

        dialog_thread = threading.Thread(target=run_dialog)
        dialog_thread.start()

    def show_about_dialog(self, icon, item):
        def run_dialog():
            root = tk.Tk()
            root.withdraw()

            dialog = tk.Toplevel(root)
            dialog.title("About")
            dialog.resizable(False, False)
            label = tk.Label(dialog, text="PowerToys Run Enhance\nVersion: 0.0.4\nAuthor: Illustar0")
            label.pack(pady=10)

            def open_github():
                webbrowser.open("https://github.com/Illustar0/PowerToysRunEnhance")

            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=5)

            visit_button = tk.Button(button_frame, text="Visit GitHub", command=open_github)
            visit_button.pack(side=tk.LEFT, padx=5)
            close_button = tk.Button(button_frame, text="Close", command=dialog.destroy)
            close_button.pack(side=tk.LEFT, padx=5)
            dialog.geometry("+%d+%d" % (root.winfo_screenwidth() / 2 - 150, root.winfo_screenheight() / 2 - 50))

            root.mainloop()

        dialog_thread = threading.Thread(target=run_dialog)
        dialog_thread.start()

    def show_config_dialog(self, icon, item):
        def run_dialog():
            '''
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Config", f"searchWindowName={self.searchWindowName}\npowerToysRunHotKey={self.powerToysRunHotKey}\nautoFocus={self.autoFocus}")
            root.destroy()
            '''
            root = tk.Tk()
            root.withdraw()
            dialog = tk.Toplevel(root)
            dialog.title("Config")
            dialog.resizable(False, False)
            text = tk.Text(dialog, wrap=tk.WORD, width=50, height=20)
            text.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
            text.tag_configure("key", foreground="blue")
            text.tag_configure("string", foreground="green")
            text.tag_configure("comment", foreground="grey")
            with open('config.toml', 'r', encoding='utf-8') as file:
                config_content = file.read()
            text.insert(tk.END, config_content)

            highlight_toml(text)
            text.config(state=tk.DISABLED)
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=10)

            close_button = tk.Button(button_frame, text="Close", command=dialog.destroy)
            close_button.pack(side=tk.LEFT, padx=5)

            dialog.geometry("+%d+%d" % (root.winfo_screenwidth() / 2 - 250, root.winfo_screenheight() / 2 - 150))
            root.mainloop()

        dialog_thread = threading.Thread(target=run_dialog)
        dialog_thread.start()

    def on_keyboard_event(self, event):
        if self.stopHook:
            return True
        if event.WindowName == self.searchWindowName and self.enabled:
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
                    self.stopHook = False
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
            pystray.MenuItem("About", self.show_about_dialog),
            pystray.MenuItem("Config", self.show_config_dialog),
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
