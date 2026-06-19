"""Input simulation via ctypes SendInput + pywinauto keyboard."""
from __future__ import annotations
import ctypes
import ctypes.wintypes
import time
from pywinauto import Desktop

user32 = ctypes.windll.user32

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000
KEYEVENTF_KEYUP = 0x0002
WHEEL_DELTA = 120
SM_CXSCREEN, SM_CYSCREEN = 0, 1


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG), ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD), ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD), ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD), ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD), ("union", _INPUT_UNION)]


def _send_input(*inputs: INPUT):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(arr), arr, ctypes.sizeof(INPUT))


def _mouse_input(flags, data=0, x=0, y=0) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_MOUSE
    cx = user32.GetSystemMetrics(SM_CXSCREEN)
    cy = user32.GetSystemMetrics(SM_CYSCREEN)
    inp.union.mi.dx = int(x * 65535 / cx) if cx else x
    inp.union.mi.dy = int(y * 65535 / cy) if cy else y
    inp.union.mi.mouseData = data
    inp.union.mi.dwFlags = flags | MOUSEEVENTF_ABSOLUTE
    return inp


def _key_input(vk, up=False) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    inp.union.ki.dwFlags = KEYEVENTF_KEYUP if up else 0
    return inp


VK_MAP = {
    "enter": 0x0D, "return": 0x0D, "tab": 0x09, "escape": 0x1B, "esc": 0x1B,
    "space": 0x20, "backspace": 0x08, "delete": 0x2E, "del": 0x2E,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74,
    "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79,
    "f11": 0x7A, "f12": 0x7B,
    "ctrl": 0xA2, "control": 0xA2, "shift": 0xA0, "alt": 0xA4,
    "win": 0x5B, "insert": 0x2D,
}


def _activate(hwnd: int):
    """Bring window to foreground."""
    user32.SetForegroundWindow(hwnd)
    ctypes.windll.kernel32.Sleep(100)


def _client_to_screen(hwnd: int, x: int, y: int) -> tuple[int, int]:
    """Convert client-relative coordinates to screen coordinates."""
    point = ctypes.wintypes.POINT(x, y)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y


def click(hwnd: int, x: int, y: int, button: str = "left", count: int = 1):
    """Click at window client-area coordinates."""
    _activate(hwnd)
    sx, sy = _client_to_screen(hwnd, x, y)

    if button in ("left", "l"):
        down_f, up_f = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    elif button in ("right", "r"):
        down_f, up_f = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    else:
        down_f, up_f = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP

    for _ in range(count):
        _send_input(_mouse_input(down_f, x=sx, y=sy), _mouse_input(up_f, x=sx, y=sy))


def drag(hwnd: int, from_x: int, from_y: int, to_x: int, to_y: int, button: str = "left"):
    """Drag from one position to another."""
    _activate(hwnd)
    fsx, fsy = _client_to_screen(hwnd, from_x, from_y)
    tsx, tsy = _client_to_screen(hwnd, to_x, to_y)

    if button in ("left", "l"):
        down_f, up_f = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    elif button in ("right", "r"):
        down_f, up_f = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    else:
        down_f, up_f = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP

    _send_input(_mouse_input(down_f, x=fsx, y=fsy))
    steps = max(abs(to_x - from_x), abs(to_y - from_y), 1)
    for i in range(1, steps + 1):
        ix = fsx + (tsx - fsx) * i // steps
        iy = fsy + (tsy - fsy) * i // steps
        _send_input(_mouse_input(MOUSEEVENTF_MOVE, x=ix, y=iy))
    _send_input(_mouse_input(up_f, x=tsx, y=tsy))


def scroll(hwnd: int, x: int, y: int, scroll_y: int = 0, scroll_x: int = 0):
    """Scroll at position. Positive scroll_y = up, negative = down."""
    _activate(hwnd)
    sx, sy = _client_to_screen(hwnd, x, y)
    _send_input(_mouse_input(MOUSEEVENTF_MOVE, x=sx, y=sy))

    if scroll_y:
        _send_input(_mouse_input(MOUSEEVENTF_WHEEL, data=scroll_y * WHEEL_DELTA))


def type_text(hwnd: int, text: str):
    """Type text into a window using pywinauto's keyboard handling."""
    _activate(hwnd)
    win = Desktop(backend="uia").window(handle=hwnd)
    win.type_keys(text, with_spaces=True, set_foreground=False)


def press_key(hwnd: int, key: str):
    """Press a key or chord (e.g. 'ctrl+a', 'ctrl+shift+s', 'enter')."""
    _activate(hwnd)

    parts = [p.strip().lower() for p in key.split("+")]
    vk_sequence: list[tuple[int, bool]] = []

    for part in parts:
        if part in VK_MAP:
            vk_sequence.append((VK_MAP[part], False))
        elif len(part) == 1:
            vk = user32.VkKeyScanW(ord(part)) & 0xFF
            vk_sequence.append((vk, False))
        else:
            raise ValueError(f"Unknown key: {part}")

    for vk, _ in vk_sequence:
        _send_input(_key_input(vk, up=False))
    for vk, _ in reversed(vk_sequence):
        _send_input(_key_input(vk, up=True))


def set_value(hwnd: int, x: int, y: int, value: str):
    """Click an element then replace its content with value."""
    click(hwnd, x, y)
    time.sleep(0.2)
    press_key(hwnd, "ctrl+a")
    type_text(hwnd, value)
