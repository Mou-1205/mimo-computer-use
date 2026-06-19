# MiMo-Computer-Use

<div align="center">

[![Version](https://img.shields.io/npm/v/mimo-computer-use?style=flat-square&logo=npm&color=CB3837)](https://github.com/Mou-1205/mimo-computer-use)
[![License](https://img.shields.io/badge/许可证-MIT-blue?style=flat-square)](LICENSE)
[![Lang](https://img.shields.io/badge/Lang-中文-007EC6?style=flat-square)](.) [![Lang](https://img.shields.io/badge/Lang-English-007EC6?style=flat-square)](README.md)

> [MiMoCode](https://github.com/Mou-1205/mimo-computer-use) 的 Windows 桌面自动化技能 — 通过截图、UI 无障碍树检查和输入模拟控制任意 Windows 应用。

</div>

## 平台支持

| 平台 | 状态 |
|------|------|
| Windows 10/11 | ✅ 已支持 |
| macOS | ❌ 暂无开发计划 |

> 本技能依赖 Windows 特有的 API（`PrintWindow`、`SendInput`、`UI Automation`、`EnumWindows`），无法在 macOS 或 Linux 上运行。

## 功能

`mimo-computer-use` 让 MiMoCode 像人类一样与 Windows 桌面应用交互 — 截图、读取 UI 元素、点击、输入、滚动、拖拽。

**没有 API？没有 CLI？没关系。** 人能看到并点击的东西，这个技能都能自动化。

### 实际应用场景

| 场景 | 技能能做什么 |
|------|-------------|
| **发送微信消息** | 打开微信 → 搜索联系人 → 输入并发送 |
| **填写桌面表单** | 截图表单 → 读取字段 → 输入数据 → 提交 |
| **自动化 Excel/Word** | 打开文件 → 导航单元格 → 编辑 → 保存 |
| **浏览器测试** | 启动浏览器 → 点击元素 → 验证截图 |
| **文件管理** | 打开资源管理器 → 导航 → 重命名/移动文件 |
| **控制播放器** | 找到播放器窗口 → 点击播放/暂停/跳过 |
| **老旧应用自动化** | 与没有现代 API 的应用交互 |

## 工作原理

本项目灵感来源于 [OpenAI Codex Computer Use](https://openai.com/index/computer-use/) 插件，该插件通过 `@oai/sky` 运行时和 Named Pipe IPC 为 Codex 提供桌面自动化能力。

`mimo-computer-use` 使用纯 Python 技术栈重新实现了相同的核心原理：

| Codex Computer Use | MiMo-Computer-Use |
|--------------------|-------------------|
| `@oai/sky` 运行时 | `pywinauto` + `ctypes` |
| Named Pipe IPC | 直接 Python CLI |
| Node REPL 执行 | Bash 工具执行 |
| `Windows.Graphics.Capture` | `PrintWindow` API |
| `UI Automation` via sky | `pywinauto` UIA 后端 |
| `SendInput` via sky | `ctypes.SendInput` |

**核心工作流：** 截图 → 读取 UI 树 → 模拟输入 → 验证结果

Agent 截图来"看到"屏幕，读取无障碍树来"理解"界面结构，然后通过输入注入来"执行"操作 — 点击、输入、滚动或拖拽。每次操作后通过截图验证结果。

## 安装

### 前置要求

- **Windows 10/11**
- **Python 3.10+**
- **MiMoCode** (`npm install -g @mimo-ai/cli`)

### 通过 npm 安装

```bash
npm install -g mimo-computer-use
```

### 从源码安装

```bash
git clone https://github.com/Mou-1205/mimo-computer-use.git
cd mimo-computer-use
python -m pip install pywinauto mss Pillow psutil
```

### 复制到 MiMoCode 技能目录

```bash
# 默认技能位置
# C:\Users\<用户名>\.agents\skills\mimo-computer-use\
```

## 快速开始

```bash
# 列出所有运行中的应用
python scripts/cu.py apps

# 按标题查找窗口
python scripts/cu.py find "记事本"

# 全屏截图
python scripts/cu.py screenshot --full -o screenshot.png

# 截取特定窗口（即使被遮挡也能截取）
python scripts/cu.py screenshot --title "记事本" -o notepad.png

# 读取 UI 无障碍树
python scripts/cu.py uitree --title "记事本"

# 点击坐标
python scripts/cu.py click --title "记事本" --x 100 --y 200

# 输入文字
python scripts/cu.py type --title "记事本" --text "你好，世界！"

# 按键盘快捷键
python scripts/cu.py key --title "记事本" --key "ctrl+s"
```

## 命令参考

### 窗口发现

| 命令 | 说明 |
|------|------|
| `apps` | 列出所有运行中的应用（按进程分组） |
| `find <pattern>` | 按标题查找窗口（正则，不区分大小写） |
| `activate --hwnd N` / `--title P` | 将窗口激活到前台 |
| `launch <exe_path>` | 通过路径启动应用 |

### 截图

| 命令 | 说明 |
|------|------|
| `screenshot --hwnd N [-o path]` | 截取窗口（被遮挡也能截取） |
| `screenshot --title "App" [-o path]` | 按标题模式截取 |
| `screenshot --full [-o path]` | 截取整个主屏幕 |
| `screenshot --base64` | 返回 base64 而非文件 |

### UI 树

| 命令 | 说明 |
|------|------|
| `uitree --hwnd N [--max-depth N]` | 读取无障碍树 |

返回带 `[index]` 的缩进元素列表、坐标和属性。

### 输入操作

| 命令 | 说明 |
|------|------|
| `click --hwnd N --x X --y Y` | 点击坐标 |
| `click --hwnd N --x X --y Y --button right` | 右键点击 |
| `click --hwnd N --x X --y Y --count 2` | 双击 |
| `type --hwnd N --text "hello"` | 输入文字 |
| `key --hwnd N --key "ctrl+s"` | 按键或组合键 |
| `scroll --hwnd N --x X --y Y --scroll-y N` | 滚动（正=上，负=下） |
| `drag --hwnd N --from-x X1 --from-y Y1 --to-x X2 --to-y Y2` | 拖拽 |
| `set-value --hwnd N --x X --y Y --value "text"` | 点击元素，全选，输入 |

### 组合命令

| 命令 | 说明 |
|------|------|
| `inspect --hwnd N [-o path]` | 一次获取截图 + UI 树 |

### 按键名称

`Enter`, `Tab`, `Escape`, `Space`, `Backspace`, `Delete`, `Up`/`Down`/`Left`/`Right`, `Home`/`End`, `PageUp`/`PageDown`, `F1`-`F12`, `Ctrl`/`Shift`/`Alt`, `Insert`

组合键：`ctrl+a`, `ctrl+shift+s`, `alt+f4`

## 工作流

```
发现 → 截图 → 理解 → 操作 → 验证
apps   screenshot  uitree  click   screenshot
find                读树    type    确认结果
```

## 处理自定义渲染应用

许多应用（微信、Electron 应用、游戏）使用自定义渲染，不通过无障碍 API 暴露 UI 元素。对于这些应用：

1. **使用图像识别** — 截图后用多模态模型（如 `mimo-v2.5`）识别元素位置
2. **使用搜索/导航** — 许多应用有 `Ctrl+F` 或内置搜索
3. **避免猜测坐标** — 优先使用键盘导航而非点击

### 微信示例

```bash
# 1. 查找并激活微信
python scripts/cu.py find "微信"
python scripts/cu.py activate --hwnd <N>

# 2. 搜索联系人
python scripts/cu.py key --hwnd <N> --key "ctrl+f"
python scripts/cu.py type --hwnd <N> --text "联系人名"
python scripts/cu.py key --hwnd <N> --key "down"
python scripts/cu.py key --hwnd <N> --key "enter"

# 3. 发送消息
python scripts/cu.py click --hwnd <N> --x 400 --y 530
python scripts/cu.py type --hwnd <N> --text "你好！"
python scripts/cu.py key --hwnd <N> --key "enter"
```

## 多模态支持

对于自定义渲染应用的图像识别，使用多模态模型如 `mimo-v2.5`。

如果模型不支持图片输入，安装 [mimo-mcp-server](https://www.npmjs.com/package/mimo-mcp-server) MCP 服务器：

```bash
npm install -g mimo-mcp-server
```

## 常见问题

如果遇到任何问题，请[提交 Issue](https://github.com/Mou-1205/mimo-computer-use/issues)。

## 技术栈

| 组件 | 技术 |
|------|------|
| 窗口截图 | `PrintWindow` API (Win32) via ctypes |
| 全屏截图 | `mss`（快速跨平台） |
| UI 树读取 | `pywinauto`（UI Automation） |
| 鼠标输入 | `SendInput` API via ctypes |
| 键盘输入 | `pywinauto` `.type_keys()` |
| 窗口管理 | `EnumWindows` + `psutil` |

## 许可证

[MIT](LICENSE) © [Mou](https://github.com/Mou-1205)
