#!/usr/bin/env python3
"""MiMoCode Computer Use — Unified CLI.

Usage: python cu.py <command> [options]
Output: JSON to stdout
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from screenshot import capture_window, capture_fullscreen
from uitree import read_tree
from input_sim import click as sim_click, type_text, press_key, scroll, drag, set_value
from apps import list_windows, list_apps, find_window, activate_window, launch_app


def ok(data: dict):
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.exit(0)


def fail(msg: str):
    json.dump({"error": msg}, sys.stdout, ensure_ascii=False)
    sys.exit(1)


def save_image(img, save_path: str | None = None, as_base64: bool = False) -> dict:
    """Save image to file or return as base64."""
    if as_base64:
        import base64, io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return {"base64": base64.b64encode(buf.getvalue()).decode("ascii"),
                "width": img.width, "height": img.height}

    if not save_path:
        save_path = str(Path.home() / ".tmp" / "cu_screenshot.png")
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(save_path)
    return {"path": save_path, "width": img.width, "height": img.height}


def resolve_hwnd(args) -> int:
    """Resolve window handle from --hwnd or --title."""
    if args.hwnd:
        return args.hwnd
    if args.title:
        w = find_window(args.title)
        if not w:
            fail(f"No window found matching: {args.title}")
        return w["hwnd"]
    fail("Specify --hwnd or --title")


def cmd_screenshot(args):
    if args.full:
        img = capture_fullscreen()
    else:
        hwnd = resolve_hwnd(args)
        img = capture_window(hwnd)
    ok({"screenshot": save_image(img, args.output, getattr(args, "base64", False))})


def cmd_uitree(args):
    hwnd = resolve_hwnd(args)
    result = read_tree(hwnd, max_depth=args.max_depth)
    if result.get("error"):
        fail(result["error"])
    ok(result)


def cmd_click(args):
    hwnd = resolve_hwnd(args)
    sim_click(hwnd, args.x, args.y, button=args.button, count=args.count)
    ok({"action": "click", "x": args.x, "y": args.y, "button": args.button})


def cmd_type(args):
    hwnd = resolve_hwnd(args)
    type_text(hwnd, args.text)
    ok({"action": "type", "length": len(args.text)})


def cmd_key(args):
    hwnd = resolve_hwnd(args)
    press_key(hwnd, args.key)
    ok({"action": "key", "key": args.key})


def cmd_scroll(args):
    hwnd = resolve_hwnd(args)
    scroll(hwnd, args.x, args.y, scroll_y=args.scroll_y, scroll_x=args.scroll_x)
    ok({"action": "scroll", "x": args.x, "y": args.y,
        "scroll_x": args.scroll_x, "scroll_y": args.scroll_y})


def cmd_drag(args):
    hwnd = resolve_hwnd(args)
    drag(hwnd, args.from_x, args.from_y, args.to_x, args.to_y, button=args.button)
    ok({"action": "drag", "from": [args.from_x, args.from_y], "to": [args.to_x, args.to_y]})


def cmd_set_value(args):
    hwnd = resolve_hwnd(args)
    set_value(hwnd, args.x, args.y, args.value)
    ok({"action": "set_value", "x": args.x, "y": args.y})


def cmd_windows(_args):
    ok({"windows": list_windows()})


def cmd_apps(_args):
    ok({"apps": list_apps()})


def cmd_find(args):
    w = find_window(args.pattern)
    if w:
        ok({"found": True, "window": w})
    else:
        ok({"found": False, "pattern": args.pattern})


def cmd_activate(args):
    hwnd = resolve_hwnd(args)
    activate_window(hwnd)
    ok({"action": "activate", "hwnd": hwnd})


def cmd_launch(args):
    result = launch_app(args.command)
    if result.get("error"):
        fail(result["error"])
    time.sleep(2)
    ok(result)


def cmd_inspect(args):
    """Capture screenshot + UI tree in one call."""
    hwnd = resolve_hwnd(args)
    img = capture_window(hwnd)
    tree_result = read_tree(hwnd, max_depth=args.max_depth)
    ok({
        "screenshot": save_image(img, args.output),
        "uitree": tree_result,
    })


def main():
    p = argparse.ArgumentParser(description="MiMoCode Computer Use CLI")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("screenshot")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--full", action="store_true")
    s.add_argument("--output", "-o")
    s.add_argument("--base64", action="store_true")
    s.set_defaults(func=cmd_screenshot)

    s = sub.add_parser("uitree")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--max-depth", type=int, default=10)
    s.set_defaults(func=cmd_uitree)

    s = sub.add_parser("click")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--x", type=int, required=True)
    s.add_argument("--y", type=int, required=True)
    s.add_argument("--button", default="left", choices=["left", "right", "middle"])
    s.add_argument("--count", type=int, default=1)
    s.set_defaults(func=cmd_click)

    s = sub.add_parser("type")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--text", required=True)
    s.set_defaults(func=cmd_type)

    s = sub.add_parser("key")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--key", required=True)
    s.set_defaults(func=cmd_key)

    s = sub.add_parser("scroll")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--x", type=int, required=True)
    s.add_argument("--y", type=int, required=True)
    s.add_argument("--scroll-y", type=int, default=0)
    s.add_argument("--scroll-x", type=int, default=0)
    s.set_defaults(func=cmd_scroll)

    s = sub.add_parser("drag")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--from-x", type=int, required=True)
    s.add_argument("--from-y", type=int, required=True)
    s.add_argument("--to-x", type=int, required=True)
    s.add_argument("--to-y", type=int, required=True)
    s.add_argument("--button", default="left")
    s.set_defaults(func=cmd_drag)

    s = sub.add_parser("set-value")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--x", type=int, required=True)
    s.add_argument("--y", type=int, required=True)
    s.add_argument("--value", required=True)
    s.set_defaults(func=cmd_set_value)

    s = sub.add_parser("windows")
    s.set_defaults(func=cmd_windows)

    s = sub.add_parser("apps")
    s.set_defaults(func=cmd_apps)

    s = sub.add_parser("find")
    s.add_argument("pattern")
    s.set_defaults(func=cmd_find)

    s = sub.add_parser("activate")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.set_defaults(func=cmd_activate)

    s = sub.add_parser("launch")
    s.add_argument("command")
    s.set_defaults(func=cmd_launch)

    s = sub.add_parser("inspect")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--title")
    s.add_argument("--output", "-o")
    s.add_argument("--max-depth", type=int, default=10)
    s.set_defaults(func=cmd_inspect)

    args = p.parse_args()
    if not args.command:
        p.print_help()
        fail("No command specified")
    args.func(args)


if __name__ == "__main__":
    main()
