"""Screenshot capture engine for Windows."""
import ctypes
import ctypes.wintypes
import mss
from PIL import Image

PW_RENDERFULLCONTENT = 0x00000002


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", ctypes.wintypes.WORD),
        ("biBitCount", ctypes.wintypes.WORD),
        ("biCompression", ctypes.wintypes.DWORD),
        ("biSizeImage", ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", ctypes.wintypes.DWORD),
        ("biClrImportant", ctypes.wintypes.DWORD),
    ]


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

for _fn, _restype, _argtypes in [
    (user32.GetWindowDC, ctypes.wintypes.HDC, [ctypes.wintypes.HWND]),
    (user32.ReleaseDC, ctypes.c_int, [ctypes.wintypes.HWND, ctypes.wintypes.HDC]),
    (gdi32.CreateCompatibleDC, ctypes.wintypes.HDC, [ctypes.wintypes.HDC]),
    (gdi32.CreateCompatibleBitmap, ctypes.wintypes.HBITMAP,
     [ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int]),
    (gdi32.SelectObject, ctypes.wintypes.HGDIOBJ,
     [ctypes.wintypes.HDC, ctypes.wintypes.HGDIOBJ]),
    (gdi32.DeleteObject, ctypes.wintypes.BOOL, [ctypes.wintypes.HGDIOBJ]),
    (gdi32.DeleteDC, ctypes.wintypes.BOOL, [ctypes.wintypes.HDC]),
    (user32.PrintWindow, ctypes.wintypes.BOOL,
     [ctypes.wintypes.HWND, ctypes.wintypes.HDC, ctypes.c_uint]),
    (user32.GetClientRect, ctypes.wintypes.BOOL,
     [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]),
    (user32.IsIconic, ctypes.wintypes.BOOL, [ctypes.wintypes.HWND]),
    (user32.GetSystemMetrics, ctypes.c_int, [ctypes.c_int]),
    (gdi32.GetDIBits, ctypes.c_int,
     [ctypes.wintypes.HDC, ctypes.wintypes.HBITMAP,
      ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p,
      ctypes.POINTER(BITMAPINFOHEADER), ctypes.c_uint]),
]:
    _fn.restype = _restype
    _fn.argtypes = _argtypes


def capture_window(hwnd: int) -> Image.Image:
    """Capture a window screenshot via PrintWindow. Works for occluded windows."""
    if user32.IsIconic(hwnd):
        raise ValueError("Window is minimized. Restore it first or use --full.")

    rect = ctypes.wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise ValueError(f"GetClientRect failed for hwnd {hwnd}")

    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w <= 0 or h <= 0:
        raise ValueError(f"Window has zero size: {w}x{h}")

    hdc_win = user32.GetWindowDC(hwnd)
    if not hdc_win:
        raise ValueError(f"GetWindowDC failed for hwnd {hwnd}")

    hdc_mem = hbitmap = None
    try:
        hdc_mem = gdi32.CreateCompatibleDC(hdc_win)
        hbitmap = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
        old = gdi32.SelectObject(hdc_mem, hbitmap)

        ok = user32.PrintWindow(hwnd, hdc_mem, PW_RENDERFULLCONTENT)
        if not ok:
            ok = user32.PrintWindow(hwnd, hdc_mem, 0)
        if not ok:
            raise ValueError(f"PrintWindow failed for hwnd {hwnd}")

        gdi32.SelectObject(hdc_mem, old)

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth, bmi.biHeight = w, -h
        bmi.biPlanes, bmi.biBitCount, bmi.biCompression = 1, 32, 0

        buf = ctypes.create_string_buffer(w * h * 4)
        if not gdi32.GetDIBits(hdc_mem, hbitmap, 0, h, buf, ctypes.byref(bmi), 0):
            raise ValueError(f"GetDIBits failed for hwnd {hwnd}")
        return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    finally:
        if hbitmap:
            gdi32.DeleteObject(hbitmap)
        if hdc_mem:
            gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(hwnd, hdc_win)


def capture_fullscreen() -> Image.Image:
    """Capture full primary screen via mss (fast)."""
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[1])
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
