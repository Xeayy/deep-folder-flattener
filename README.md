# Deep Folder Flattener · 深层子文件夹文件一键提取平铺工具

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011-0078D6.svg)](#环境要求)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)](#环境要求)

一个 Windows 桌面小工具：把多层嵌套文件夹里的文件**一键剪切到根目录摊平**，重名自动改名不覆盖，顺手清理被掏空的子目录。

A Windows desktop utility that flattens deeply nested folders — move every file to the root directory in one click, auto-rename duplicates instead of overwriting, and clean up emptied subdirectories. Built with Python 3 + tkinter, standard library only.

面向需要频繁处理素材包、下载目录、归档文件夹的场景（电商素材、设计稿件、会议资料等）。单文件 exe，免安装、不联网。

![界面预览](docs/screenshot.png)

## 功能

- **一键平铺**：递归遍历所有子文件夹，将文件剪切移动到所选根目录，保留原文件名与内容
- **重名保护**：冲突时自动命名为 `原名_(1).扩展名`、`_(2)`… 依次递增；Windows 下使用 `os.rename`，同名目标必然失败而非覆盖
- **空目录清理**：可选，仅删除确认为空的子目录（`os.rmdir` 非空必失败），绝不删除根目录
- **隐藏内容可选**：默认跳过隐藏文件/文件夹，可勾选处理（识别 Windows 隐藏属性与点开头文件）
- **拖拽导入**：从资源管理器拖文件夹到窗口即可填入路径（Win32 `WM_DROPFILES`）
- **后台执行**：遍历与移动在线程中完成，界面不阻塞；日志分级着色（成功/重名/跳过/异常）
- **异常隔离**：单个文件权限不足、被占用等异常记录后继续，不中断整体任务

## 环境要求

- Windows 10 / 11（64 位）
- 运行 exe：无需 Python、无需联网
- 从源码运行：Python 3.8+，仅标准库（tkinter）

## 快速开始

```bash
python main.py
```

或直接运行打包后的 `深层子文件夹文件一键提取平铺工具.exe`。

## 使用方式

1. 选择目标根文件夹：拖入窗口、点「浏览...」或手动输入路径
2. 按需勾选三个选项（默认：自动重命名开、清理空目录开、处理隐藏项关）
3. 点「开始一键平铺提取」，确认提示后等待完成
4. 查看日志与汇总（扫描数 / 提取数 / 重名数 / 清理目录数 / 跳过 / 异常 / 耗时）

> 移动操作不可撤销，执行前请备份重要数据。程序会拒绝把磁盘根目录作为目标。

## 技术实现

| 模块 | 说明 |
|---|---|
| UI | `tkinter` + `ttk`，自定义样式与字号层级；窗口尺寸按 DPI 自适应并可手动缩放 |
| 高分屏 | `SetProcessDpiAwarenessContext`（Per-Monitor V2）→ `SetProcessDpiAwareness` → `SetProcessDPIAware` 逐级降级 |
| 线程模型 | `threading.Thread` 执行遍历/移动，`queue.Queue` + `after()` 回传日志与统计，避免跨线程操作控件 |
| 拖放 | `DragAcceptFiles` + `SetWindowLongPtrW` 子类化窗口过程拦截 `WM_DROPFILES`，`DragQueryFileW` 读取 Unicode 路径，退出前还原窗口过程 |
| 防覆盖 | 目标存在则生成 `stem_(n).ext`；`os.rename` 在 Windows 上不覆盖已存在文件 |
| 进度条 | Canvas 自绘（品牌蓝、圆角、不定进度动画），避免系统主题强制绿色 |
| 资源 | 图标经 PyInstaller `--add-data` 内嵌，运行时经 `sys._MEIPASS` 解析 |

## 目录结构

```
.
├── main.py            # 全部源码（单文件）
├── app_icon.ico       # 应用图标（多尺寸）
├── docs/
│   └── screenshot.png # 界面截图
├── .gitignore
└── README.md
```

## 打包

```bash
pyinstaller --noconfirm --clean --onefile --windowed ^
  --icon app_icon.ico --add-data "app_icon.ico;." ^
  --name "深层子文件夹文件一键提取平铺工具" main.py
```

## 已知限制

- 仅支持 Windows；拖拽依赖 Win32 消息，非跨平台实现
- 不跟随符号链接/目录联接，避免越出目标根目录或循环遍历
- 移动操作无内置撤销，依赖用户备份
- 目标为网络路径时，扫描速度取决于网络状况

## 版本记录

| 版本 | 变更 |
|---|---|
| v1.3.0 | 新增文件夹拖拽导入；Canvas 自绘进度条（修复空闲残留绿块）；长路径从开头显示；字号层级与间距重排；窗口可缩放并自适应内容 |
| v1.2.0 | 补全交付文档；示例目录；稳定性修复 |
| v1.1.0 | 重名保护、空目录清理、隐藏项选项 |

## 许可证

本项目基于 [MIT License](LICENSE) 开源发布，可自由使用、修改、分发与商用，保留版权与许可声明即可。

## 贡献

欢迎提交 Issue 反馈问题，或 Pull Request 改进功能。提交前请确保：

- 保持零第三方运行依赖（仅 Python 标准库）
- 改动集中在 `main.py`，并在 PR 描述中说明动机与测试方式
- 涉及文件移动的逻辑，请补充手动验证步骤（含重名、权限不足、隐藏文件等边界场景）

## 致谢

感谢所有提交 Issue 与建议的使用者。
