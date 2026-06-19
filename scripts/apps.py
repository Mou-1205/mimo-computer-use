"""Application and window management."""
from __future__ import annotations
import ctypes
import ctypes.wintypes
import re
import subprocess
import psutil

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
DWMWA_CLOAKED = 14


def _is_window_visible(hwnd: int) -> bool:
    if not user32.IsWindowVisible(hwnd):
        return False
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if ex_style & WS_EX_TOOLWINDOW:
        cloaked = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
        if cloaked.value:
            return False
    length = user32.GetWindowTextLengthW(hwnd)
    return length > 0


def _get_window_info(hwnd: int) -> dict | None:
    if not _is_window_visible(hwnd):
        return None
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return None
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value

    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))

    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    is_min = bool(user32.IsIconic(hwnd))
    try:
        proc = psutil.Process(pid.value)
        proc_name = proc.name()
    except Exception:
        proc_name = ""

    return {
        "hwnd": hwnd, "title": title, "pid": pid.value,
        "process": proc_name, "minimized": is_min,
        "rect": {"left": rect.left, "top": rect.top,
                 "right": rect.right, "bottom": rect.bottom},
    }


def list_windows() -> list[dict]:
    """List all visible windows."""
    results: list[dict] = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

    def callback(hwnd, _):
        info = _get_window_info(hwnd)
        if info:
            results.append(info)
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return results


def list_apps() -> list[dict]:
    """List running applications grouped by process name."""
    windows = list_windows()
    app_map: dict[str, dict] = {}
    for w in windows:
        name = w["process"] or w["title"]
        if name not in app_map:
            app_map[name] = {"name": name, "windows": []}
        app_map[name]["windows"].append({
            "hwnd": w["hwnd"], "title": w["title"],
            "minimized": w["minimized"], "rect": w["rect"],
        })
    return list(app_map.values())


def find_window(pattern: str) -> dict | None:
    """Find first window whose title contains pattern (case-insensitive)."""
    pat = re.compile(pattern, re.IGNORECASE)
    for w in list_windows():
        if pat.search(w["title"]):
            return w
    return None


def activate_window(hwnd: int) -> bool:
    """Bring a window to foreground and restore if minimized."""
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)
    return bool(user32.SetForegroundWindow(hwnd))


def launch_app(exe_or_name: str) -> dict:
    """Launch an application by exe path or name."""
    try:
        proc = subprocess.Popen(exe_or_name, shell=False)
        return {"pid": proc.pid, "command": exe_or_name, "error": None}
    except Exception as e:
        return {"pid": None, "command": exe_or_name, "error": str(e)}
