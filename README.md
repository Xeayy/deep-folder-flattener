# Deep Folder Flattener

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078D6.svg)](#requirements)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)](#requirements)
[![Dependencies](https://img.shields.io/badge/dependencies-none-success.svg)](#requirements)

**English** | [简体中文](README.zh-CN.md)

A Windows desktop utility that flattens deeply nested folders: move every file from subdirectories into the root folder in one click, auto-rename name collisions instead of overwriting, and clean up the emptied subdirectories.

Built with Python 3 and tkinter — **standard library only**, no third-party dependencies, no network access.

![Screenshot](docs/screenshot.png)

## Why

Material packs, downloads and archives usually arrive nested several levels deep (`pack/main/white-bg/01.jpg`). Collecting those files by hand means dozens of cut-and-paste operations, and same-named files silently overwrite each other. This tool does it in one pass, safely.

## Features

- **One-click flatten** — recursively walks every subdirectory and moves files to the chosen root, keeping original names and content
- **Collision-safe** — duplicates are renamed `name_(1).ext`, `_(2)`, …; on Windows `os.rename` refuses to overwrite an existing target, so a file is never silently replaced
- **Empty-directory cleanup** — optional; only directories confirmed empty are removed (`os.rmdir` fails on non-empty dirs)
- **Optional hidden files** — hidden files/folders are skipped by default; can be included (Windows hidden attribute and dot-prefixed names)
- **Drag & drop** — drop a folder from Explorer onto the window to fill in the path (`WM_DROPFILES`)
- **Responsive UI** — traversal and moves run on a worker thread; logs stream back through a queue with level-based colors (moved / conflict / skipped / error)
- **Fault tolerant** — permission errors and locked files are logged and skipped; the batch continues
- **HiDPI aware** — Per-Monitor V2 DPI awareness, plus DPI-scaled layout and fonts

## Requirements

| | |
|---|---|
| OS | Windows 10 / 11 (64-bit) |
| Run the exe | No Python, no installation, no network |
| Run from source | Python 3.8+, tkinter (bundled with python.org builds) |

## Getting started

Download `DeepFolderFlattener-v1.3.0.exe` from [Releases](../../releases) and run it, or start from source:

```bash
python main.py
```

## Usage

1. Pick the target root folder — drag it onto the window, click **浏览...** (Browse), or type the path directly
2. Choose the options (defaults: auto-rename on, cleanup on, hidden files off)
3. Click **开始一键平铺提取** (Start) and confirm the warning dialog
4. Review the log and the summary (scanned / moved / renamed conflicts / cleaned dirs / skipped / errors / elapsed)

The app refuses filesystem roots (e.g. `D:\`) as targets, since flattening an entire drive is almost never intended.

> Moving files is not undoable. Back up important data before running, and try the sample folder first.

## How it works

| Area | Implementation |
|---|---|
| UI | tkinter + ttk with a custom style layer, fixed type scale, resizable window with content-aware initial size |
| HiDPI | `SetProcessDpiAwarenessContext` (Per-Monitor V2) → `SetProcessDpiAwareness` → `SetProcessDPIAware` fallback chain |
| Threading | `threading.Thread` for traversal/moves; `queue.Queue` + `after()` marshals logs and stats back to the UI thread |
| Drag & drop | `DragAcceptFiles` + window-procedure subclassing for `WM_DROPFILES`, paths read via `DragQueryFileW`; original procedure restored on exit |
| Collision safety | Generate `stem_(n).ext`; `os.rename` on Windows never replaces an existing file |
| Progress bar | Canvas-drawn (rounded, brand color, indeterminate animation) instead of the themed system bar |
| Icon | Bundled via PyInstaller `--add-data`, resolved at runtime through `sys._MEIPASS` |

## Project structure

```
.
├── main.py            # entire application (single file)
├── app_icon.ico       # multi-size application icon
├── docs/
│   └── screenshot.png # UI screenshot
├── LICENSE
├── .gitignore
├── README.md
└── README.zh-CN.md
```

## Build

```bash
pyinstaller --noconfirm --clean --onefile --windowed ^
  --icon app_icon.ico --add-data "app_icon.ico;." ^
  --name "DeepFolderFlattener" main.py
```

## Known limitations

- Windows only — drag & drop relies on Win32 messages
- Symlinks and directory junctions are not followed (prevents escaping the target root or loops)
- No built-in undo; rely on backups
- Network shares work, but scan speed depends on throughput

## Changelog

| Version | Changes |
|---|---|
| v1.3.0 | Folder drag & drop; Canvas progress bar (fixes leftover green segment); long paths displayed from the start; new type scale and spacing; resizable window with content-aware sizing |
| v1.2.0 | Delivery documentation, sample directory, stability fixes |
| v1.1.0 | Collision protection, empty-directory cleanup, hidden-file option |

## License

[MIT](LICENSE) © 2026 Ilana

## Contributing

Issues and pull requests are welcome. Please keep the project dependency-free (standard library only), keep changes focused in `main.py`, and describe manual verification steps for file-move logic (duplicate names, permission errors, hidden files).
