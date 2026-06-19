# MiMo-Computer-Use

<div align="center">

[![Version](https://img.shields.io/npm/v/mimo-computer-use?style=flat-square&logo=npm&color=CB3837)](https://github.com/Mou-1205/mimo-computer-use)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Lang](https://img.shields.io/badge/Lang-English-007EC6?style=flat-square)](.) [![Lang](https://img.shields.io/badge/Lang-中文-007EC6?style=flat-square)](README_zh.md)

> Windows Desktop Automation Skill for [MiMoCode](https://github.com/XiaomiMiMo/MiMo-Code) — Control Any Windows Application Through Screenshots, UI Accessibility Tree Inspection, and Input Simulation.

</div>

## Platform Support

| Platform | Status |
|----------|--------|
| Windows 10/11 | ✅ Supported |
| macOS | ❌ No Plans |

> This skill relies on Windows-specific APIs (`PrintWindow`, `SendInput`, `UI Automation`, `EnumWindows`) and cannot run on macOS or Linux.

## What It Does

`mimo-computer-use` lets MiMoCode agents interact with Windows desktop applications as a human would — by taking screenshots, reading UI elements, clicking, typing, scrolling, and dragging.

**No API? No CLI? No Problem.** If a human can see it and click it, this skill can automate it.

### Real-World Use Cases

| Scenario | What the Skill Does |
|----------|---------------------|
| **Send WeChat Messages** | Open WeChat → Search Contact → Type & Send |
| **Fill Desktop Forms** | Capture Form → Read Fields → Type Data → Submit |
| **Automate Excel/Word** | Open File → Navigate Cells → Edit → Save |
| **Browser Testing** | Launch Browser → Click Elements → Verify Screenshots |
| **File Management** | Open Explorer → Navigate → Rename/Move Files |
| **Control Media Players** | Find Player Window → Click Play/Pause/Skip |
| **Legacy App Automation** | Interact with Apps That Have No Modern API |

## How It Works

This skill is inspired by [OpenAI's Codex Computer Use](https://github.com/openai/codex) plugin, which provides desktop automation for Codex through the `@oai/sky` runtime and Named Pipe IPC on Windows.

`mimo-computer-use` reimplements the same core principles using a pure Python stack:

| Codex Computer Use | MiMo-Computer-Use |
|--------------------|-------------------|
| `@oai/sky` runtime | `pywinauto` + `ctypes` |
| Named Pipe IPC | Direct Python CLI |
| Node REPL execution | Bash tool execution |
| `Windows.Graphics.Capture` | `PrintWindow` API |
| `UI Automation` via sky | `pywinauto` UIA backend |
| `SendInput` via sky | `ctypes.SendInput` |

**Core workflow:** Screenshot → Read UI Tree → Simulate Input → Verify Result

The agent captures a screenshot to "see" the screen, reads the accessibility tree to "understand" the UI structure, then uses input injection to "act" — click, type, scroll, or drag. Each action is verified with a follow-up screenshot.

## Installation

### Prerequisites

- **Windows 10/11**
- **Python 3.10+**
- **MiMoCode** (`npm install -g @mimo-ai/cli`)

### Install via npm

```bash
npm install -g mimo-computer-use
```

### Install from Source

```bash
git clone https://github.com/Mou-1205/mimo-computer-use.git
cd mimo-computer-use
python -m pip install pywinauto mss Pillow psutil
```

### Copy to MiMoCode Skills Directory

```bash
# Default Skills Location
# C:\Users\<you>\.agents\skills\mimo-computer-use\
```

## Quick Start

```bash
# List All Running Applications
python scripts/cu.py apps

# Find a Window by Title
python scripts/cu.py find "Notepad"

# Take a Fullscreen Screenshot
python scripts/cu.py screenshot --full -o screenshot.png

# Capture a Specific Window (Works Even If Occluded)
python scripts/cu.py screenshot --title "Notepad" -o notepad.png

# Read the UI Accessibility Tree
python scripts/cu.py uitree --title "Notepad"

# Click at Coordinates
python scripts/cu.py click --title "Notepad" --x 100 --y 200

# Type Text
python scripts/cu.py type --title "Notepad" --text "Hello, World!"

# Press Keyboard Shortcuts
python scripts/cu.py key --title "Notepad" --key "ctrl+s"
```

## Commands

### Window Discovery

| Command | Description |
|---------|-------------|
| `apps` | List All Running Apps Grouped by Process |
| `find <pattern>` | Find Window by Title (Regex, Case-Insensitive) |
| `activate --hwnd N` / `--title P` | Bring Window to Foreground |
| `launch <exe_path>` | Launch Application by Path |

### Screenshot

| Command | Description |
|---------|-------------|
| `screenshot --hwnd N [-o path]` | Capture Window (Works If Occluded) |
| `screenshot --title "App" [-o path]` | Capture by Title Pattern |
| `screenshot --full [-o path]` | Capture Entire Primary Screen |
| `screenshot --base64` | Return as Base64 Instead of File |

### UI Tree

| Command | Description |
|---------|-------------|
| `uitree --hwnd N [--max-depth N]` | Read Accessibility Tree |

Returns indented element list with `[index]`, coordinates, and properties.

### Input Actions

| Command | Description |
|---------|-------------|
| `click --hwnd N --x X --y Y` | Click at Coordinates |
| `click --hwnd N --x X --y Y --button right` | Right-Click |
| `click --hwnd N --x X --y Y --count 2` | Double-Click |
| `type --hwnd N --text "hello"` | Type Text |
| `key --hwnd N --key "ctrl+s"` | Press Key or Chord |
| `scroll --hwnd N --x X --y Y --scroll-y N` | Scroll (Positive=Up, Negative=Down) |
| `drag --hwnd N --from-x X1 --from-y Y1 --to-x X2 --to-y Y2` | Drag Between Points |
| `set-value --hwnd N --x X --y Y --value "text"` | Click, Select All, Type |

### Combined

| Command | Description |
|---------|-------------|
| `inspect --hwnd N [-o path]` | Screenshot + UI Tree in One Call |

### Key Names

`Enter`, `Tab`, `Escape`, `Space`, `Backspace`, `Delete`, `Up`/`Down`/`Left`/`Right`, `Home`/`End`, `PageUp`/`PageDown`, `F1`-`F12`, `Ctrl`/`Shift`/`Alt`, `Insert`

Chords: `ctrl+a`, `ctrl+shift+s`, `alt+f4`

## Workflow

```
Discover → Capture → Understand → Act → Verify
  apps     screenshot   uitree     click   screenshot
  find                  read tree  type    confirm
```

## Handling Custom-Rendered Apps

Many apps (WeChat, Electron apps, games) use custom rendering that doesn't expose UI elements through accessibility APIs. For these apps:

1. **Use Image Recognition** — Take a screenshot, then use a multimodal model (e.g. `mimo-v2.5`) to identify element positions
2. **Use Search/Navigation** — Many apps have `Ctrl+F` or built-in search
3. **Avoid Guessing Coordinates** — Prefer keyboard navigation over clicking

### WeChat Example

```bash
# 1. Find and Activate WeChat
python scripts/cu.py find "微信"
python scripts/cu.py activate --hwnd <N>

# 2. Search for a Contact
python scripts/cu.py key --hwnd <N> --key "ctrl+f"
python scripts/cu.py type --hwnd <N> --text "ContactName"
python scripts/cu.py key --hwnd <N> --key "down"
python scripts/cu.py key --hwnd <N> --key "enter"

# 3. Send a Message
python scripts/cu.py click --hwnd <N> --x 400 --y 530
python scripts/cu.py type --hwnd <N> --text "Hello!"
python scripts/cu.py key --hwnd <N> --key "enter"
```

## Multimodal Support

For image recognition on custom-rendered apps, use a multimodal model like `mimo-v2.5`.

If your model doesn't support image input natively, install the [mimo-mcp-server](https://www.npmjs.com/package/mimo-mcp-server) MCP server:

```bash
npm install -g mimo-mcp-server
```

## FAQ

If you encounter any issues, please [submit an issue](https://github.com/Mou-1205/mimo-computer-use/issues).

## Tech Stack

| Component | Technology |
|-----------|------------|
| Window Capture | `PrintWindow` API (Win32) via ctypes |
| Fullscreen Capture | `mss` (Fast Cross-Platform) |
| UI Tree Reading | `pywinauto` (UI Automation) |
| Mouse Input | `SendInput` API via ctypes |
| Keyboard Input | `pywinauto` `.type_keys()` |
| Window Management | `EnumWindows` + `psutil` |

## License

[MIT](LICENSE) © [Mou](https://github.com/Mou-1205)
