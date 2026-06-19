"""UI Automation tree reader using pywinauto."""
from __future__ import annotations
from pywinauto import Desktop


def get_element_info(ctrl) -> dict:
    """Extract key properties from a UIA control."""
    info: dict = {}
    try:
        info["control_type"] = ctrl.element_info.control_type or ""
    except Exception:
        info["control_type"] = ""
    for prop in ("automation_id", "class_name", "name"):
        try:
            val = getattr(ctrl.element_info, prop, None)
            if val:
                info[prop] = str(val)
        except Exception:
            pass
    try:
        r = ctrl.element_info.rectangle
        info["rect"] = {"l": r.left, "t": r.top, "r": r.right, "b": r.bottom}
    except Exception:
        pass
    try:
        if hasattr(ctrl.element_info, "is_enabled") and not ctrl.element_info.is_enabled:
            info["disabled"] = True
    except Exception:
        pass
    return info


def build_tree(ctrl, depth: int = 0, max_depth: int = 10, index: list[int] | None = None) -> str:
    """Build indented accessibility tree text with element indexes."""
    if index is None:
        index = [0]
    if depth > max_depth:
        return ""

    idx = index[0]
    index[0] += 1
    info = get_element_info(ctrl)
    ctype = info.get("control_type", "")
    name = info.get("name", "")
    aid = info.get("automation_id", "")
    rect = info.get("rect")
    disabled = info.get("disabled", False)

    parts = [f"[{idx}] {ctype}"]
    if name:
        parts.append(f'"{name[:80]}"')
    if aid:
        parts.append(f"id={aid}")
    if rect:
        parts.append(f"({rect['l']},{rect['t']},{rect['r']},{rect['b']})")
    if disabled:
        parts.append("[disabled]")
    line = "  " * depth + " ".join(parts)

    lines = [line]
    try:
        for child in ctrl.children():
            child_text = build_tree(child, depth + 1, max_depth, index)
            if child_text:
                lines.append(child_text)
    except Exception:
        pass
    return "\n".join(lines)


def get_focused_info(ctrl) -> str | None:
    """Get focused element description."""
    try:
        focused = ctrl.get_focus()
        if focused:
            info = get_element_info(focused)
            return f"{info.get('control_type', '')} \"{info.get('name', '')}\""
    except Exception:
        pass
    return None


def get_selected_info(ctrl) -> list[str]:
    """Get selected elements description."""
    results = []
    try:
        for sel in ctrl.get_selection():
            info = get_element_info(sel)
            results.append(f"{info.get('control_type', '')} \"{info.get('name', '')}\"")
    except Exception:
        pass
    return results


def read_tree(hwnd: int, max_depth: int = 10) -> dict:
    """Read UI tree from a window handle.

    Returns {"tree": str, "focused": str|None, "selected": [str], "error": str|None}
    """
    try:
        app_obj = Desktop(backend="uia")
        win = app_obj.window(handle=hwnd)
        win.wait("exists", timeout=5)

        tree_text = build_tree(win, max_depth=max_depth)
        focused = get_focused_info(win)
        selected = get_selected_info(win)

        return {"tree": tree_text, "focused": focused, "selected": selected, "error": None}
    except Exception as e:
        return {"tree": "", "focused": None, "selected": [], "error": str(e)}
