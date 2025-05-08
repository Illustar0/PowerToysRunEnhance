import win32api
import win32con
import win32process


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
