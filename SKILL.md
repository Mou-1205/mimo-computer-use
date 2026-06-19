---
name: mimo-computer-use
description: >
  Control Windows desktop applications from MiMoCode. Automate any Windows app
  via screenshots, UI accessibility tree reading, and input simulation (click,
  type, scroll, drag, keypress). Use when: (1) automating desktop app workflows,
  (2) reading/interacting with app UI elements, (3) capturing window screenshots,
  (4) listing/launching/switching between applications. Triggers: "desktop automation",
  "control Windows app", "automate UI", "take screenshot of window", "click on",
  "type in", "interact with app".
---

# MiMoCode Computer Use

Automate Windows desktop applications through screenshots, UI tree inspection, and input injection.

## Setup

Install dependencies once:

```bash
python -m pip install pywinauto mss Pillow psutil --quiet
```

## Core Workflow

1. **Discover** — `apps` or `find` to locate the target window
2. **Capture** — `screenshot` to see the current state
3. **Understand** — `uitree` to read the accessibility tree
4. **Act** — `click`, `type`, `key`, `scroll`, `drag` to interact
5. **Verify** — `screenshot` again to confirm the result

## CLI Reference

All commands: `python <skill-dir>/scripts/cu.py <command> [options]`
Output: JSON to stdout. Errors: `{"error": "..."}` with exit code 1.

### Window Discovery

| Command | Description |
|---------|-------------|
| `apps` | List all running apps grouped by process |
| `find <pattern>` | Find window by title (regex, case-insensitive) |
| `activate --hwnd N` or `--title P` | Bring window to foreground |
| `launch <exe_path>` | Launch application by path |

### Screenshot

| Command | Description |
|---------|-------------|
| `screenshot --hwnd N [-o path]` | Capture window (works if occluded) |
| `screenshot --title "Notepad" [-o path]` | Capture by title pattern |
| `screenshot --full [-o path]` | Capture entire primary screen |

Returns: `{"screenshot": {"path": "...", "width": N, "height": N}}`

### UI Tree

| Command | Description |
|---------|-------------|
| `uitree --hwnd N [--max-depth N]` | Read accessibility tree |

Returns: `{"tree": "...", "focused": "...", "selected": [...], "error": null}`

Tree format: indented element list with `[index]` for each element:
```
[0] Window "My App"
  [1] MenuBar
    [2] MenuItem "File"
    [3] MenuItem "Edit"
  [4] Edit "Document content" (100,50,700,500)
```

### Input Actions

| Command | Description |
|---------|-------------|
| `click --hwnd N --x X --y Y [--button left\|right\|middle] [--count N]` | Click at coordinates |
| `type --hwnd N --text "hello"` | Type text (pywinauto handles special chars) |
| `key --hwnd N --key "ctrl+s"` | Press key or chord |
| `scroll --hwnd N --x X --y Y --scroll-y N` | Scroll (positive=up, negative=down) |
| `drag --hwnd N --from-x X1 --from-y Y1 --to-x X2 --to-y Y2` | Drag between points |
| `set-value --hwnd N --x X --y Y --value "text"` | Click element, select all, type value |

### Combined

| Command | Description |
|---------|-------------|
| `inspect --hwnd N [--max-depth N] [-o path]` | Screenshot + UI tree in one call |

## Key Names

Enter/Return, Tab, Escape, Space, Backspace, Delete, Up/Down/Left/Right,
Home/End, PageUp/PageDown, F1-F12, Ctrl/Shift/Alt, Insert

Chords: `ctrl+a`, `ctrl+shift+s`, `alt+f4`

## Guidelines

- Use `find` or `apps` first to discover the target window, not hardcoded hwnd values.
- After `uitree`, use the `[index]` to identify element positions, then compute coordinates from the `rect` field.
- Batch related input actions between screenshots to minimize latency.
- After actions that change layout, capture a new screenshot/uitree before the next action.
- Use `--title` pattern matching instead of raw `--hwnd` when the window title is known.
- For text entry, click the target input field first, then `type`.
- Use `key` for keyboard shortcuts and control keys; use `type` for text content.
- `click` coordinates are **client-area relative** (0,0 = top-left of window content). The `rect` fields from `uitree` are **screen-absolute**. To convert: `click_x = rect.left - client_origin_x`.
- Use `inspect` to get both screenshot and UI tree in one call when you need to understand an app's state.

## Handling Custom-Rendered Apps (WeChat, Electron, etc.)

Many apps (WeChat, Electron apps, games) use custom rendering that does NOT expose chat lists, canvas content, or custom widgets through UI Automation. For these apps:

1. **Use image recognition** — take a `screenshot`, then use vision to identify element positions
2. **Use search/navigation** — many apps have `Ctrl+F` or built-in search; use `key` to activate, `type` to search, `↓`+`Enter` to select
3. **Avoid guessing coordinates** — vision-estimated coordinates often have ±20px误差; prefer keyboard navigation over clicking

### WeChat Workflow Example

```
# 1. Find and activate WeChat
find "微信" → activate --hwnd N

# 2. Open search and find contact
key --hwnd N --key "ctrl+f"
type --hwnd N --text "某人"
key --hwnd N --key "down"      # navigate to correct result
key --hwnd N --key "enter"     # select

# 3. Type and send message
click --hwnd N --x 400 --y 530   # click input area
type --hwnd N --text "你好"
key --hwnd N --key "enter"       # send
```

### When UI Tree Is Empty

If `uitree` returns no useful elements (common for chat apps, browsers, games):
1. Take a `screenshot` and use image recognition to find element positions
2. Use `key` commands (Tab, Enter, arrows, Ctrl+F) for keyboard-driven navigation
3. Use `click` with coordinates from image recognition as a last resort

## Multimodal Model Recommendation

Image recognition is essential for custom-rendered apps. Use a multimodal model (e.g. `mimo-v2.5`) that supports `understand_image` natively.

If your current model does NOT support image input, install the `mimo-mcp-server` MCP server to add multimodal capabilities:

```bash
# Install globally
npm install -g mimo-mcp-server

# Or add to MiMoCode config
# C:\Users\Administrator\.config\mimocode\config.json → "mcp" key
```

**MCP server tools:**
- `mimo-mcp-server_understand_image` — analyze screenshots, identify UI elements, read text
- `mimo-mcp-server_understand_audio` — analyze audio content
- `mimo-mcp-server_understand_video` — analyze video content
- `mimo-mcp-server_speech_recognition` — speech-to-text
- `mimo-mcp-server_speech_synthesis_preset` — text-to-speech

**Source:** `C:\Users\Administrator\Documents\Mou\MCP\mimo-mcp-server\`
**npm:** https://www.npmjs.com/package/mimo-mcp-server

### Image Recognition Workflow

```
# 1. Capture screenshot
screenshot --hwnd N -o C:\path\to\screenshot.png

# 2. Use multimodal model to analyze (via MCP or native vision)
# Ask: "What are the UI elements and their pixel coordinates?"

# 3. Use returned coordinates for click/type actions
click --hwnd N --x <vision_x> --y <vision_y>
```
