# -*- coding: utf-8 -*-
"""
深层子文件夹文件一键提取平铺工具（视觉升级版）

仅使用 Python 3.x 内置标准库，无需安装任何第三方依赖。
功能：将目标根文件夹下所有子文件夹中的文件剪切移动到根目录，
      自动处理重名、可选处理隐藏文件，并可清理提取后的空目录。

视觉优化要点：
  1) 启用 Windows 高 DPI 感知，修复高分辨率屏幕下界面发虚、模糊的问题；
  2) 窗口支持手动调整宽高（内容随窗口自适应伸缩），并按 DPI 缩放默认尺寸；
  3) 统一使用微软雅黑 UI 字体体系，建立 标题14 / 分区10加粗 / 正文9.5 三级字阶；
  4) 采用低饱和现代配色（石板灰 + 品牌蓝 + 浅蓝点缀），层级分明、柔和不花哨；
  5) 日志按级别着色（成功绿/警告橙/错误红/跳过灰），一眼可辨。
"""

import errno
import os
import queue
import shutil
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

# ---------------------------------------------------------------------------
# 设计规范（Design Tokens）：集中管理字号与配色，保证全局风格统一
# ---------------------------------------------------------------------------
FONT_FAMILY = "Microsoft YaHei UI"

C_TITLE = "#0F172A"      # 主标题：近黑石板色，层级最高
C_TEXT = "#334155"       # 正文：深石板灰，柔和不刺眼
C_SUBTLE = "#64748B"     # 次要文字/说明：中灰
C_BORDER = "#E2E8F0"     # 卡片描边：极浅灰
C_ACCENT = "#2563EB"     # 品牌蓝：主操作按钮
C_ACCENT_HOVER = "#1D4ED8"
C_SOFT_ACCENT = "#EFF6FF"  # 柔和浅蓝点缀：进度槽等浅色高亮
C_LOG_BG = "#F8FAFC"       # 日志底色：极浅蓝灰，阅读舒适
C_LOG_OK = "#16A34A"     # 日志-成功：柔和绿
C_LOG_WARN = "#D97706"   # 日志-警告：柔和橙
C_LOG_ERROR = "#DC2626"  # 日志-错误：警示红
C_LOG_SKIP = "#94A3B8"   # 日志-跳过：浅灰
C_LOG_INFO = "#475569"   # 日志-常规：深灰蓝
C_BAR_TROUGH = "#E2EDFD"  # 进度条轨道：比底色略深，保证可见但不抢眼

BASE_WIDTH = 560   # 基准逻辑宽度（96 DPI 下）
BASE_HEIGHT = 480  # 基准逻辑高度

# ---------------------------------------------------------------------------
# 多语言文案：zh = 简体中文，en = English
# 默认跟随系统 UI 语言，可在标题栏右侧手动切换
# ---------------------------------------------------------------------------
I18N = {
    "zh": {
        "app_title": "深层子文件夹文件一键提取平铺工具",
        "header_subtitle": "深层素材一键归集 · 自动重命名防覆盖 · 智能清理空目录",
        "section_target": " 目标位置 ",
        "section_options": " 运行选项 ",
        "section_log": " 运行日志 ",
        "label_root": "根文件夹",
        "browse": " 浏览... ",
        "opt_rename": "遇到重名文件自动重命名（原文件名_(1).扩展名，依次递增）",
        "opt_cleanup": "提取完成后清理已掏空的子文件夹（仅删除空目录）",
        "opt_hidden": "处理隐藏文件及隐藏子文件夹",
        "start": "开始一键平铺提取",
        "author": "作者: Ilana",
        "lang_switch": "EN",
        "status_ready": "就绪 · 请选择或直接把文件夹拖入窗口",
        "status_running": "正在提取，请稍候……",
        "status_done": "任务完成",
        "status_failed": "任务异常终止",
        "status_drop_running": "任务进行中，无法更换目标文件夹",
        "status_drop_file": "请拖入文件夹，而不是文件",
        "status_drop_invalid": "拖入内容无效",
        "status_drop_ok": "已通过拖拽设置目标文件夹",
        "dlg_notice_title": "提示",
        "dlg_no_path": "请先选择目标根文件夹。",
        "dlg_invalid_title": "路径无效",
        "dlg_invalid_body": "所选文件夹不存在或不可访问，请重新选择。",
        "dlg_root_title": "安全提示",
        "dlg_root_body": "为避免误整理整个磁盘，请选择磁盘内的具体文件夹。",
        "dlg_confirm_title": "确认执行平铺提取",
        "dlg_confirm_body": (
            "此操作会将所有子文件夹内的文件剪切移动至目标根目录，"
            "原目录结构将被改变。\n\n建议在操作前备份重要数据。是否继续？"
        ),
        "dlg_close_title": "任务正在运行",
        "dlg_close_body": "请等待当前提取任务完成后再关闭程序。",
        "dlg_browse_title": "请选择目标根文件夹",
        "dlg_done_body": "平铺提取任务已完成！",
        "dlg_fail_title": "任务异常终止",
        "dlg_fail_body": "发生严重异常：{err}",
        "log_target": "目标根文件夹：{path}",
        "log_started": "任务已启动，正在后台扫描并提取文件……",
        "log_fatal": "[严重异常] 任务已终止：{err}",
        "log_walk_error": "[异常] 无法访问目录 {path}：{err}",
        "log_skip_link": "[跳过] 链接目录：{path}",
        "log_skip_hidden_dir": "[跳过] 隐藏子文件夹：{path}",
        "log_skip_hidden_file": "[跳过] 隐藏文件：{path}",
        "log_skip_special": "[跳过] 非普通文件：{path}",
        "log_move_failed": "[异常] 移动失败 {path}：{err}",
        "log_process_failed": "[异常] 处理失败 {path}：{err}",
        "log_finished": "文件提取任务执行完毕。",
        "log_exists_skip": "[跳过] 根目录已存在同名文件：{name}",
        "log_conflict": "[重名冲突] 已为文件寻找新名称：{name}",
        "log_moved": "[已移动] {src}  ->  {dst}",
        "log_race_skip": "[跳过] 同名文件竞争冲突：{name}",
        "log_cleaned": "[已清理] 空文件夹：{path}",
        "log_clean_failed": "[异常] 无法清理空文件夹 {path}：{err}",
        "log_summary": "任务汇总：\n{body}",
        "log_drop_running": "[拖拽] 任务运行中，已忽略本次拖入",
        "log_drop_file": "[拖拽] 已忽略：拖入的是文件而非文件夹：{path}",
        "log_drop_invalid": "[拖拽] 已忽略：无效的拖入项：{path}",
        "log_drop_ok": "[拖拽] 已导入目标文件夹：{path} {note}",
        "log_drop_root_warn": "[拖拽] 注意：拖入的是磁盘根目录，开始整理前会被安全检查拦截",
        "drop_ignored_note": "（已忽略其余 {n} 项）",
        "sum_scanned": "累计扫描文件数：{n}",
        "sum_moved": "成功提取数：{n}",
        "sum_conflicts": "重名冲突数：{n}",
        "sum_cleaned": "清理空文件夹数：{n}",
        "sum_skipped": "跳过项目数：{n}",
        "sum_errors": "异常数：{n}",
        "sum_elapsed": "耗时：{t:.2f} 秒",
        "err_permission": "权限不足或文件正被其他程序占用；{err}",
        "unknown_path": "未知路径",
        "unknown": "未知",
    },
    "en": {
        "app_title": "Deep Folder Flattener",
        "header_subtitle": "Collect nested files · Never overwrite · Clean empty folders",
        "section_target": " Target folder ",
        "section_options": " Options ",
        "section_log": " Log ",
        "label_root": "Folder",
        "browse": " Browse... ",
        "opt_rename": "Auto-rename duplicates (name_(1).ext, increasing)",
        "opt_cleanup": "Remove emptied subfolders afterwards (empty folders only)",
        "opt_hidden": "Include hidden files and folders",
        "start": "Start flattening",
        "author": "Author: Ilana",
        "lang_switch": "中文",
        "status_ready": "Ready · Choose a folder or drag one into the window",
        "status_running": "Working, please wait…",
        "status_done": "Completed",
        "status_failed": "Aborted due to an error",
        "status_drop_running": "A task is running; target folder can't be changed",
        "status_drop_file": "Please drop a folder, not a file",
        "status_drop_invalid": "Unsupported drop content",
        "status_drop_ok": "Target folder set by drag & drop",
        "dlg_notice_title": "Notice",
        "dlg_no_path": "Please select a target root folder first.",
        "dlg_invalid_title": "Invalid path",
        "dlg_invalid_body": "The selected folder does not exist or is not accessible.",
        "dlg_root_title": "Safety check",
        "dlg_root_body": "To avoid flattening an entire drive, pick a folder inside it.",
        "dlg_confirm_title": "Confirm flattening",
        "dlg_confirm_body": (
            "This will move every file from the subfolders into the target root "
            "and change the folder structure.\n\nBack up important data first. Continue?"
        ),
        "dlg_close_title": "Task running",
        "dlg_close_body": "Please wait for the current task to finish before closing.",
        "dlg_browse_title": "Select target root folder",
        "dlg_done_body": "Flattening completed!",
        "dlg_fail_title": "Task aborted",
        "dlg_fail_body": "A fatal error occurred: {err}",
        "log_target": "Target root: {path}",
        "log_started": "Task started; scanning and moving files in the background…",
        "log_fatal": "[FATAL] Task aborted: {err}",
        "log_walk_error": "[ERROR] Cannot access folder {path}: {err}",
        "log_skip_link": "[SKIP] Linked folder: {path}",
        "log_skip_hidden_dir": "[SKIP] Hidden folder: {path}",
        "log_skip_hidden_file": "[SKIP] Hidden file: {path}",
        "log_skip_special": "[SKIP] Not a regular file: {path}",
        "log_move_failed": "[ERROR] Move failed {path}: {err}",
        "log_process_failed": "[ERROR] Processing failed {path}: {err}",
        "log_finished": "Flattening finished.",
        "log_exists_skip": "[SKIP] Same name already exists in root: {name}",
        "log_conflict": "[CONFLICT] Finding a new name for: {name}",
        "log_moved": "[MOVED] {src}  ->  {dst}",
        "log_race_skip": "[SKIP] Name collision while moving: {name}",
        "log_cleaned": "[CLEANED] Empty folder: {path}",
        "log_clean_failed": "[ERROR] Cannot remove empty folder {path}: {err}",
        "log_summary": "Summary:\n{body}",
        "log_drop_running": "[DROP] A task is running; this drop was ignored",
        "log_drop_file": "[DROP] Ignored: dropped item is a file, not a folder: {path}",
        "log_drop_invalid": "[DROP] Ignored: unsupported item: {path}",
        "log_drop_ok": "[DROP] Target folder set: {path} {note}",
        "log_drop_root_warn": "[DROP] Note: this is a drive root and will be rejected by the safety check",
        "drop_ignored_note": "({n} other item(s) ignored)",
        "sum_scanned": "Files scanned: {n}",
        "sum_moved": "Files moved: {n}",
        "sum_conflicts": "Rename conflicts: {n}",
        "sum_cleaned": "Empty folders removed: {n}",
        "sum_skipped": "Items skipped: {n}",
        "sum_errors": "Errors: {n}",
        "sum_elapsed": "Elapsed: {t:.2f} s",
        "err_permission": "Permission denied or file is in use; {err}",
        "unknown_path": "unknown path",
        "unknown": "unknown",
    },
}


def detect_language():
    """跟随系统 UI 语言：中文系统用中文，其余默认英文。"""
    if os.name == "nt":
        try:
            import ctypes

            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if (lang_id & 0x3FF) == 0x04:  # LANG_CHINESE
                return "zh"
            return "en"
        except Exception:
            pass
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(key, "")
        if value:
            return "zh" if value.lower().startswith("zh") else "en"
    return "en"


def enable_windows_dpi_awareness():
    """启用 Windows 高 DPI 感知，从根源解决 tkinter 界面模糊问题。

    若不开启，Windows 会对窗口做位图拉伸，导致文字和控件发虚。
    """
    if os.name != "nt":
        return
    try:
        import ctypes
        try:
            # Per-Monitor V2 感知（Windows 10 1703+），缩放切换时也保持清晰
            ctypes.windll.user32.SetProcessDpiAwarenessContext(
                ctypes.c_void_p(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            )
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 系统 DPI 感知
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()  # 旧系统兜底
    except Exception:
        pass  # 感知设置失败不影响功能，仅可能在高分屏上略微软


def get_ui_scale(root):
    """获取当前系统缩放系数（96 DPI 为基准，1.25/1.5/2.0 等）。"""
    try:
        scale = root.winfo_fpixels("1i") / 96.0
    except Exception:
        scale = 1.0
    return max(1.0, round(scale * 4) / 4)  # 按 0.25 步进取整，避免奇数尺寸


# ---------------------------------------------------------------------------
# Windows 资源管理器拖放支持（WM_DROPFILES，纯标准库 ctypes 实现）
# ---------------------------------------------------------------------------
WM_DROPFILES = 0x0233   # 拖放消息：用户把文件/文件夹拖到窗口上松手
GWLP_WNDPROC = -4       # 窗口过程索引，用于子类化窗口


def get_toplevel_hwnd(widget):
    """获取 Tk 控件所属顶层窗口的 HWND（winfo_id 返回的是内部子窗口）。"""
    import ctypes

    return ctypes.windll.user32.GetParent(widget.winfo_id())


def enable_folder_dragdrop(hwnd, on_paths):
    """启用拖放到顶层窗口，回调 on_paths(paths_list) 接收拖入的路径列表。

    通过 DragAcceptFiles + 子类化窗口过程拦截 WM_DROPFILES 实现；
    返回还原函数（退出前调用，防止关闭程序时崩溃）；失败返回 None。
    """
    if os.name != "nt" or not hwnd:
        return None
    try:
        import ctypes

        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32

        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.SetWindowLongPtrW.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t
        ]
        user32.CallWindowProcW.restype = ctypes.c_ssize_t
        user32.CallWindowProcW.argtypes = [
            ctypes.c_ssize_t, ctypes.c_void_p, ctypes.c_uint,
            ctypes.c_ssize_t, ctypes.c_ssize_t,
        ]
        # DragQueryFileW / DragFinish / DragAcceptFiles 均导出自 shell32.dll
        shell32.DragQueryFileW.restype = ctypes.c_uint
        shell32.DragQueryFileW.argtypes = [
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_wchar_p, ctypes.c_uint
        ]
        shell32.DragFinish.argtypes = [ctypes.c_void_p]
        shell32.DragAcceptFiles.argtypes = [ctypes.c_void_p, ctypes.c_int]

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t, ctypes.c_ssize_t, ctypes.c_uint,
            ctypes.c_ssize_t, ctypes.c_ssize_t,
        )
        old_proc = user32.GetWindowLongPtrW(hwnd, GWLP_WNDPROC)

        def query_paths(hdrop):
            """从 HDROP 句柄中取出全部拖入项的 Unicode 路径并释放句柄。"""
            count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
            paths = []
            for index in range(count):
                length = shell32.DragQueryFileW(hdrop, index, None, 0)
                buf = ctypes.create_unicode_buffer(length + 1)
                shell32.DragQueryFileW(hdrop, index, buf, length + 1)
                paths.append(buf.value)
            shell32.DragFinish(hdrop)
            return paths

        def wnd_proc(hwindow, msg, wparam, lparam):
            """窗口过程：拦截拖放消息，其余消息原样交还原处理函数。"""
            if msg == WM_DROPFILES:
                try:
                    on_paths(query_paths(wparam))
                except Exception:
                    pass  # 拖放回调异常不得影响窗口消息循环
                return 0
            return user32.CallWindowProcW(old_proc, hwindow, msg, wparam, lparam)

        proc_ref = WNDPROC(wnd_proc)  # 引用保存在闭包中，防止被垃圾回收
        user32.SetWindowLongPtrW(
            hwnd, GWLP_WNDPROC, ctypes.cast(proc_ref, ctypes.c_void_p).value
        )
        shell32.DragAcceptFiles(hwnd, True)

        def restore():
            """还原默认窗口过程并取消拖放注册。"""
            shell32.DragAcceptFiles(hwnd, False)
            user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, old_proc)

        return restore
    except Exception:
        return None  # 拖放属增强体验，初始化失败不影响主功能


class SlimProgressBar(tk.Canvas):
    """自绘细进度条：品牌蓝填充 + 不定进度动画。

    不用 ttk.Progressbar 的原因：Windows vista 主题会强制使用系统绿色，
    且数值归零后仍会残留一小段绿色起笔，与整体配色不统一。
    """

    def __init__(self, master, height=8, color="#2563EB", trough="#EFF6FF", bg="#F1F5F9"):
        super().__init__(master, height=height, bg=bg, highlightthickness=0, bd=0)
        self._height = height
        self._color = color
        self._trough = trough
        self._animating = False
        self._pos = 0.0
        self.bind("<Configure>", lambda _event: self._draw())

    def start(self, interval=16):
        """开始不定进度动画（来回循环的蓝色滑块）。"""
        if self._animating:
            return
        self._animating = True
        self._tick(interval)

    def stop(self):
        """停止动画并清空填充，空闲时只剩浅色轨道。"""
        self._animating = False
        self._pos = 0.0
        self._draw()

    def _tick(self, interval):
        if not self._animating:
            return
        self._pos = (self._pos + 0.018) % 1.0
        self._draw()
        self.after(interval, lambda: self._tick(interval))

    def _draw(self):
        self.delete("all")
        width = self.winfo_width()
        height = self._height
        if width <= 1:
            return
        radius = height / 2
        self._rounded(0, 0, width, height, radius, self._trough)
        if self._animating:
            segment = max(width * 0.26, 60)
            left = self._pos * (width + segment) - segment
            x0, x1 = max(0, left), min(width, left + segment)
            if x1 > x0:
                self._rounded(x0, 0, x1, height, radius, self._color)

    def _rounded(self, x0, y0, x1, y1, radius, color):
        """用弧线 + 矩形拼出圆角条，避免锯齿感。"""
        self.create_oval(x0, y0, x0 + 2 * radius, y1, fill=color, outline="")
        self.create_oval(x1 - 2 * radius, y0, x1, y1, fill=color, outline="")
        self.create_rectangle(x0 + radius, y0, x1 - radius, y1, fill=color, outline="")


class FlattenFilesApp:
    """桌面程序主窗口及后台任务调度。"""

    def __init__(self, root, scale=1.0):
        self.root = root
        self.scale = scale
        self.lang = detect_language()  # 界面语言：默认跟随系统，可手动切换
        self.root.title(self.tr("app_title"))
        # 允许用户手动调整窗口大小；初始尺寸在界面构建后按内容自动适配
        self.root.configure(bg="#F1F5F9")  # 浅灰画布底色，衬托白色卡片
        self.root.resizable(True, True)

        # 界面与后台线程通过队列通信，避免子线程直接操作 tkinter 控件。
        self.event_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False
        self._dragdrop_restore = None  # 拖放注册还原函数（退出时调用）

        self.path_var = tk.StringVar()
        self.auto_rename_var = tk.BooleanVar(value=True)
        self.cleanup_var = tk.BooleanVar(value=True)
        self.include_hidden_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value=self.tr("status_ready"))

        self._setup_style()
        self._build_ui()

        # 依据界面内容的真实需求尺寸自适应窗口：保证默认状态下全部内容
        # 完整显示，不出现裁切、遮挡或需要滚动才能看到关键信息的情况。
        self.root.update_idletasks()
        win_w = max(int(BASE_WIDTH * scale), self.root.winfo_reqwidth())
        win_h = max(int(BASE_HEIGHT * scale), self.root.winfo_reqheight())
        self.root.minsize(int(win_w * 0.8), int(win_h * 0.75))

        # 首次启动时将窗口居中显示（水平居中，略偏上更符合视觉习惯）
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(
            f"{win_w}x{win_h}"
            f"+{max(0, (screen_w - win_w) // 2)}+{max(0, (screen_h - win_h) // 3)}"
        )

        # 注册资源管理器拖放支持：把文件夹直接拖进窗口即可设为目标路径
        if os.name == "nt":
            self._dragdrop_restore = enable_folder_dragdrop(
                get_toplevel_hwnd(self.root), self._on_drop_paths
            )

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._poll_events)

    # ------------------------------------------------------------------
    # 界面构建
    # ------------------------------------------------------------------
    def _setup_style(self):
        """配置 ttk 主题、字体层级与控件样式，统一视觉语言。"""
        style = ttk.Style(self.root)
        try:
            style.theme_use("vista")  # Windows 原生主题，控件渲染最精致
        except tk.TclError:
            pass  # 非 Windows 环境回退默认主题

        s = int(round(9.5 * self.scale))  # 正文字号（按 DPI 缩放）
        style.configure(".", font=(FONT_FAMILY, s), background="#F1F5F9")
        style.configure("TFrame", background="#F1F5F9")
        style.configure(
            "Card.TLabelframe",
            background="#FFFFFF",
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background="#FFFFFF",
            foreground="#334155",
            font=(FONT_FAMILY, int(round(10 * self.scale)), "bold"),
        )
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("Card.TLabel", background="#FFFFFF", foreground=C_TEXT)
        style.configure("Card.TCheckbutton", background="#FFFFFF", foreground=C_TEXT)
        style.configure("Card.TEntry", padding=2)
        style.configure("TLabel", foreground=C_TEXT)
        style.configure("Subtle.TLabel", foreground=C_SUBTLE)
        style.configure(
            "Subtitle.TLabel",
            font=(FONT_FAMILY, int(round(9 * self.scale))),
            foreground=C_SUBTLE,
        )
        style.configure(
            "Author.TLabel",
            font=(FONT_FAMILY, int(round(8 * self.scale))),
            foreground=C_SUBTLE,
        )
        style.configure(
            "Title.TLabel",
            font=(FONT_FAMILY, int(round(14 * self.scale)), "bold"),
            foreground=C_TITLE,
        )
        style.configure(
            "Horizontal.TProgressbar",
            thickness=int(8 * self.scale),
            troughcolor=C_SOFT_ACCENT,
            background=C_ACCENT,
            borderwidth=0,
        )

    def _build_ui(self):
        """创建并布局全部界面控件（三段式版式：页头 / 卡片区 / 底栏）。"""
        pad = int(10 * self.scale)  # 统一外边距
        main = ttk.Frame(self.root, padding=pad)
        main.pack(fill=tk.BOTH, expand=True)

        # ---- 页头：标题 + 副标题 + 语言切换，建立第一视觉层级 ----
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, int(10 * self.scale)))

        # 语言切换按钮：先占住右上角，再让标题左对齐
        self.lang_button = ttk.Button(
            header, text=self.tr("lang_switch"), width=5,
            command=self._toggle_language,
        )
        self.lang_button.pack(side=tk.RIGHT, anchor=tk.N)

        self.header_title = ttk.Label(
            header, text=self.tr("app_title"), style="Title.TLabel"
        )
        self.header_title.pack(anchor=tk.W)
        self.header_subtitle = ttk.Label(
            header, text=self.tr("header_subtitle"), style="Subtitle.TLabel"
        )
        self.header_subtitle.pack(anchor=tk.W, pady=(3, 0))

        # ---- 卡片 1：目标位置 ----
        self.path_frame = ttk.Labelframe(
            main, text=self.tr("section_target"), style="Card.TLabelframe",
            padding=int(12 * self.scale),
        )
        self.path_frame.pack(fill=tk.X)
        row = ttk.Frame(self.path_frame, style="Card.TFrame")
        row.pack(fill=tk.X)
        self.root_label = ttk.Label(row, text=self.tr("label_root"), style="Card.TLabel")
        self.root_label.pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(row, textvariable=self.path_var)
        self.path_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(int(8 * self.scale), 0)
        )
        self.browse_button = ttk.Button(
            row, text=self.tr("browse"), width=int(9 * self.scale),
            command=self._browse_folder,
        )
        self.browse_button.pack(side=tk.LEFT, padx=(int(8 * self.scale), 0))

        # ---- 卡片 2：运行选项 ----
        self.option_frame = ttk.Labelframe(
            main, text=self.tr("section_options"), style="Card.TLabelframe",
            padding=int(12 * self.scale),
        )
        self.option_frame.pack(fill=tk.X, pady=(int(12 * self.scale), 0))
        self.rename_check = ttk.Checkbutton(
            self.option_frame,
            text=self.tr("opt_rename"),
            variable=self.auto_rename_var,
            style="Card.TCheckbutton",
        )
        self.rename_check.pack(anchor=tk.W)
        self.cleanup_check = ttk.Checkbutton(
            self.option_frame,
            text=self.tr("opt_cleanup"),
            variable=self.cleanup_var,
            style="Card.TCheckbutton",
        )
        self.cleanup_check.pack(anchor=tk.W, pady=(int(6 * self.scale), 0))
        self.hidden_check = ttk.Checkbutton(
            self.option_frame,
            text=self.tr("opt_hidden"),
            variable=self.include_hidden_var,
            style="Card.TCheckbutton",
        )
        self.hidden_check.pack(anchor=tk.W, pady=(int(6 * self.scale), 0))

        # ---- 底栏：主操作按钮 + 进度条 + 状态文字 ----
        # 先从窗口底部固定占位，保证无论窗口多小，操作按钮始终可见。
        bottom = ttk.Frame(main)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.start_button = tk.Button(
            bottom,
            text=self.tr("start"),
            command=self._confirm_and_start,
            font=(FONT_FAMILY, int(round(10.5 * self.scale)), "bold"),
            bg=C_ACCENT,
            fg="#FFFFFF",
            activebackground=C_ACCENT_HOVER,
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=int(22 * self.scale),
            pady=int(6 * self.scale),
        )
        self.start_button.pack(side=tk.LEFT)

        # 右下角小字署名：先占住右侧角落，再让进度区向左伸展填满剩余空间
        self.author_label = ttk.Label(
            bottom, text=self.tr("author"), style="Author.TLabel"
        )
        self.author_label.pack(side=tk.RIGHT, anchor=tk.S, padx=(int(8 * self.scale), 0))

        bar_wrap = ttk.Frame(bottom)
        bar_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(int(12 * self.scale), 0))
        self.progress = SlimProgressBar(
            bar_wrap,
            height=max(6, int(8 * self.scale)),
            bg="#F1F5F9",
            color=C_ACCENT,
            trough=C_BAR_TROUGH,
        )
        self.progress.pack(fill=tk.X)
        ttk.Label(
            bar_wrap, textvariable=self.status_var, style="Subtle.TLabel"
        ).pack(anchor=tk.W, pady=(int(3 * self.scale), 0))

        # ---- 卡片 3：运行日志（占满剩余空间，窗口缩放时随之伸缩）----
        self.log_frame = ttk.Labelframe(
            main, text=self.tr("section_log"), style="Card.TLabelframe",
            padding=int(10 * self.scale),
        )
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(int(12 * self.scale), 0))
        self.log_text = ScrolledText(
            self.log_frame,
            height=int(6 * self.scale) or 6,
            width=1,  # 宽度交给布局自适应拉伸，避免默认 80 字符宽度撑大窗口
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=(FONT_FAMILY, int(round(9.5 * self.scale))),
            background=C_LOG_BG,
            foreground=C_LOG_INFO,
            borderwidth=0,
            highlightthickness=0,
            padx=int(8 * self.scale),
            pady=int(6 * self.scale),
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        # 分级语义色：日志级别一眼可辨
        self.log_text.tag_configure("ok", foreground=C_LOG_OK)
        self.log_text.tag_configure("warn", foreground=C_LOG_WARN)
        self.log_text.tag_configure("error", foreground=C_LOG_ERROR)
        self.log_text.tag_configure("skip", foreground=C_LOG_SKIP)
        self.log_text.tag_configure("info", foreground=C_LOG_INFO)

    # ------------------------------------------------------------------
    # 多语言
    # ------------------------------------------------------------------
    def tr(self, key, **kwargs):
        """取当前语言文案；缺失时回退中文，再回退键名。"""
        table = I18N.get(self.lang, I18N["zh"])
        text = table.get(key) or I18N["zh"].get(key, key)
        return text.format(**kwargs) if kwargs else text

    def _toggle_language(self):
        """在中文与英文界面之间切换。"""
        self.lang = "en" if self.lang == "zh" else "zh"
        self._apply_language()

    def _apply_language(self):
        """刷新全部静态控件文案：不重建窗口，也不清空已有日志。"""
        self.root.title(self.tr("app_title"))
        self.lang_button.configure(text=self.tr("lang_switch"))
        self.header_title.configure(text=self.tr("app_title"))
        self.header_subtitle.configure(text=self.tr("header_subtitle"))
        self.path_frame.configure(text=self.tr("section_target"))
        self.root_label.configure(text=self.tr("label_root"))
        self.browse_button.configure(text=self.tr("browse"))
        self.option_frame.configure(text=self.tr("section_options"))
        self.rename_check.configure(text=self.tr("opt_rename"))
        self.cleanup_check.configure(text=self.tr("opt_cleanup"))
        self.hidden_check.configure(text=self.tr("opt_hidden"))
        self.log_frame.configure(text=self.tr("section_log"))
        self.start_button.configure(text=self.tr("start"))
        self.author_label.configure(text=self.tr("author"))
        if not self.is_running:
            self.status_var.set(self.tr("status_ready"))
        # 英文文案通常更宽，切换后按内容需要扩展窗口（只放大、不缩小）
        self.root.update_idletasks()
        need_w = max(self.root.winfo_width(), self.root.winfo_reqwidth())
        need_h = max(self.root.winfo_height(), self.root.winfo_reqheight())
        if need_w > self.root.winfo_width() or need_h > self.root.winfo_height():
            self.root.geometry(f"{need_w}x{need_h}")
        self._append_log(
            "Language switched to English." if self.lang == "en" else "已切换为中文界面。",
            "info",
        )

    # ------------------------------------------------------------------
    # 交互动作
    # ------------------------------------------------------------------
    def _browse_folder(self):
        """调用 Windows 原生文件夹选择对话框。"""
        selected = filedialog.askdirectory(
            parent=self.root, title=self.tr("dlg_browse_title"), mustexist=True
        )
        if selected:
            self._apply_path(os.path.normpath(selected))

    def _apply_path(self, path):
        """写入路径并让输入框从开头显示，避免长路径只剩尾部。"""
        self.path_var.set(path)
        self.root.after_idle(self._show_path_start)

    def _show_path_start(self):
        try:
            self.path_entry.icursor(0)
            self.path_entry.xview_moveto(0)
        except tk.TclError:
            pass

    def _on_drop_paths(self, paths):
        """处理拖放进窗口的路径列表（Windows 消息回调，主线程执行）。

        策略：取第一个有效文件夹作为目标；普通文件、无效项、多余项
        均记入日志并忽略；任务运行中一律忽略拖入，防止中途篡改参数。
        """
        if not paths:
            return
        if self.is_running:
            self.status_var.set(self.tr("status_drop_running"))
            self._append_log(self.tr("log_drop_running"), "warn")
            return

        folders, files, invalid = [], [], []
        for path in paths:
            try:
                if os.path.isdir(path):
                    folders.append(path)
                elif os.path.exists(path):
                    files.append(path)
                else:
                    invalid.append(path)
            except OSError:
                invalid.append(path)  # 权限/占用等导致的探测失败按无效处理

        if not folders:
            if files:
                self.status_var.set(self.tr("status_drop_file"))
                self._append_log(
                    self.tr("log_drop_file", path=files[0]), "warn"
                )
            else:
                self.status_var.set(self.tr("status_drop_invalid"))
                self._append_log(
                    self.tr(
                        "log_drop_invalid",
                        path=invalid[0] if invalid else self.tr("unknown"),
                    ),
                    "warn",
                )
            return

        # 以第一个文件夹为目标，其余项忽略并说明数量
        target = folders[0]
        ignored = len(paths) - 1
        note = self.tr("drop_ignored_note", n=ignored) if ignored > 0 else ""
        normalized = os.path.normpath(os.path.abspath(target))
        self._apply_path(normalized)
        self.status_var.set(self.tr("status_drop_ok"))
        self._append_log(self.tr("log_drop_ok", path=normalized, note=note), "info")
        # 磁盘根目录沿用现有的安全防线，此处仅提前给出直观提示
        if os.path.dirname(normalized) == normalized:
            self._append_log(self.tr("log_drop_root_warn"), "warn")

    def _confirm_and_start(self):
        """校验路径，并在用户明确确认后启动后台线程。"""
        if self.is_running:
            return

        raw_path = self.path_var.get().strip().strip('"')
        if not raw_path:
            messagebox.showwarning(
                self.tr("dlg_notice_title"), self.tr("dlg_no_path"), parent=self.root
            )
            return
        if not os.path.isdir(raw_path):
            messagebox.showerror(
                self.tr("dlg_invalid_title"),
                self.tr("dlg_invalid_body"),
                parent=self.root,
            )
            return

        target_root = os.path.abspath(raw_path)
        # 防止误选整个磁盘根目录，避免大规模整理系统或其他无关文件。
        if os.path.dirname(target_root) == target_root:
            messagebox.showwarning(
                self.tr("dlg_root_title"),
                self.tr("dlg_root_body"),
                parent=self.root,
            )
            return

        confirmed = messagebox.askokcancel(
            self.tr("dlg_confirm_title"),
            self.tr("dlg_confirm_body"),
            icon=messagebox.WARNING,
            parent=self.root,
        )
        if not confirmed:
            return

        self._set_running_state(True)
        self._clear_log()
        self._append_log(self.tr("log_target", path=target_root), "info")
        self._append_log(self.tr("log_started"), "info")

        options = {
            "auto_rename": self.auto_rename_var.get(),
            "cleanup": self.cleanup_var.get(),
            "include_hidden": self.include_hidden_var.get(),
        }
        self.worker_thread = threading.Thread(
            target=self._worker_entry,
            args=(target_root, options),
            name="FlattenFilesWorker",
            daemon=True,
        )
        self.worker_thread.start()

    # ------------------------------------------------------------------
    # 后台任务：遍历与移动逻辑（与界面完全解耦）
    # ------------------------------------------------------------------
    def _worker_entry(self, target_root, options):
        """后台线程入口；最外层兜底捕获异常，确保线程不会静默崩溃。"""
        started_at = time.perf_counter()
        stats = {
            "scanned": 0,
            "moved": 0,
            "conflicts": 0,
            "cleaned": 0,
            "skipped": 0,
            "errors": 0,
        }
        fatal_error = None
        try:
            self._flatten_folder(target_root, options, stats)
        except Exception as exc:  # 最外层保险，具体文件异常已在内部单独处理
            fatal_error = str(exc)
            stats["errors"] += 1
            self.event_queue.put(("log", "error", self.tr("log_fatal", err=exc)))
        finally:
            elapsed = time.perf_counter() - started_at
            self.event_queue.put(("done", stats, elapsed, fatal_error))

    def _flatten_folder(self, target_root, options, stats):
        """遍历并移动文件；所有文件系统异常均记录日志后继续处理。"""
        include_hidden = options["include_hidden"]
        visited_dirs = []

        def on_walk_error(exc):
            stats["errors"] += 1
            path = getattr(exc, "filename", self.tr("unknown_path"))
            self.event_queue.put(
                ("log", "error", self.tr("log_walk_error", path=path, err=exc))
            )

        # topdown=True 可在进入子目录前过滤隐藏目录及链接目录。
        for current_dir, dir_names, file_names in os.walk(
            target_root, topdown=True, onerror=on_walk_error, followlinks=False
        ):
            if current_dir != target_root:
                visited_dirs.append(current_dir)

            kept_dirs = []
            for dir_name in dir_names:
                dir_path = os.path.join(current_dir, dir_name)
                # 不跟随符号链接/目录联接，避免越出目标根目录或产生循环。
                if os.path.islink(dir_path):
                    stats["skipped"] += 1
                    self.event_queue.put(
                        ("log", "skip", self.tr("log_skip_link", path=dir_path))
                    )
                    continue
                if not include_hidden and self._is_hidden(dir_path):
                    stats["skipped"] += 1
                    self.event_queue.put(
                        ("log", "skip", self.tr("log_skip_hidden_dir", path=dir_path))
                    )
                    continue
                kept_dirs.append(dir_name)
            dir_names[:] = kept_dirs

            for file_name in file_names:
                stats["scanned"] += 1
                source_path = os.path.join(current_dir, file_name)
                try:
                    if not include_hidden and self._is_hidden(source_path):
                        stats["skipped"] += 1
                        self.event_queue.put(
                            ("log", "skip", self.tr("log_skip_hidden_file", path=source_path))
                        )
                        continue
                    # 只处理普通文件，跳过链接、设备或其他特殊项目。
                    if not os.path.isfile(source_path) or os.path.islink(source_path):
                        stats["skipped"] += 1
                        self.event_queue.put(
                            ("log", "skip", self.tr("log_skip_special", path=source_path))
                        )
                        continue
                    # 根目录已有文件无需移动，但仍计入累计扫描文件数。
                    if os.path.normpath(current_dir) == os.path.normpath(target_root):
                        continue
                    self._move_one_file(source_path, target_root, options, stats)
                except (OSError, shutil.Error) as exc:
                    stats["errors"] += 1
                    self.event_queue.put(
                        ("log", "error",
                         self.tr("log_move_failed", path=source_path,
                                 err=self._friendly_error(exc)))
                    )
                except Exception as exc:
                    stats["errors"] += 1
                    self.event_queue.put(
                        ("log", "error",
                         self.tr("log_process_failed", path=source_path, err=exc))
                    )

        if options["cleanup"]:
            self._cleanup_empty_dirs(visited_dirs, stats)
        self.event_queue.put(("log", "info", self.tr("log_finished")))

    def _move_one_file(self, source_path, target_root, options, stats):
        """移动单个文件，并依据选项严格避免覆盖任何现有文件。"""
        file_name = os.path.basename(source_path)
        destination = os.path.join(target_root, file_name)
        conflict_counted = False

        while True:
            if os.path.lexists(destination):
                if not options["auto_rename"]:
                    stats["skipped"] += 1
                    self.event_queue.put(
                        ("log", "skip", self.tr("log_exists_skip", name=file_name))
                    )
                    return
                if not conflict_counted:
                    stats["conflicts"] += 1
                    conflict_counted = True
                self.event_queue.put(
                    ("log", "warn", self.tr("log_conflict", name=file_name))
                )
                destination = self._next_available_name(destination)
                continue

            try:
                # 文件始终位于同一目标磁盘内，os.rename 在 Windows 上不会覆盖
                # 已存在的目标文件；若此刻发生竞争，会抛出 FileExistsError。
                os.rename(source_path, destination)
                stats["moved"] += 1
                self.event_queue.put(
                    ("log", "ok", self.tr("log_moved", src=source_path, dst=destination))
                )
                return
            except FileExistsError:
                # 极端情况下，检查目标后又有其他程序创建了同名文件，重新命名。
                if not options["auto_rename"]:
                    stats["skipped"] += 1
                    self.event_queue.put(
                        ("log", "skip", self.tr("log_race_skip", name=file_name))
                    )
                    return
                if not conflict_counted:
                    stats["conflicts"] += 1
                    conflict_counted = True
                destination = self._next_available_name(destination)

    @staticmethod
    def _next_available_name(destination):
        """生成 名称_(1).扩展名、名称_(2).扩展名……形式的可用路径。"""
        directory = os.path.dirname(destination)
        stem, extension = os.path.splitext(os.path.basename(destination))
        index = 1
        while True:
            candidate = os.path.join(directory, f"{stem}_({index}){extension}")
            if not os.path.lexists(candidate):
                return candidate
            index += 1

    def _cleanup_empty_dirs(self, visited_dirs, stats):
        """按由深到浅顺序删除空目录；绝不删除目标根目录。"""
        for dir_path in reversed(visited_dirs):
            try:
                os.rmdir(dir_path)  # 非空目录会失败，因此不会误删其中任何文件
                stats["cleaned"] += 1
                self.event_queue.put(
                    ("log", "ok", self.tr("log_cleaned", path=dir_path))
                )
            except OSError as exc:
                # 目录非空属于正常情况；目录已不存在则无需重复处理。
                if exc.errno in (errno.ENOTEMPTY, errno.EEXIST) or getattr(
                    exc, "winerror", None
                ) == 145:
                    continue
                if exc.errno == errno.ENOENT:
                    continue
                stats["errors"] += 1
                self.event_queue.put(
                    ("log", "error",
                     self.tr("log_clean_failed", path=dir_path,
                             err=self._friendly_error(exc)))
                )

    @staticmethod
    def _is_hidden(path):
        """识别点开头文件及 Windows 带隐藏属性的文件/文件夹。"""
        if os.path.basename(path).startswith("."):
            return True
        if os.name == "nt":
            try:
                # ctypes 属于 Python 标准库，用于读取 Windows 文件隐藏属性。
                import ctypes

                attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if attributes != 0xFFFFFFFF:  # INVALID_FILE_ATTRIBUTES
                    return bool(attributes & 0x2)  # FILE_ATTRIBUTE_HIDDEN
            except Exception:
                # 属性读取失败时不贸然排除，后续文件操作会记录真实异常。
                return False
        return False

    def _friendly_error(self, exc):
        """为常见权限、占用错误补充易读说明，同时保留原始错误信息。"""
        if isinstance(exc, PermissionError):
            return self.tr("err_permission", err=exc)
        return str(exc)

    # ------------------------------------------------------------------
    # 界面事件消费与状态管理
    # ------------------------------------------------------------------
    def _poll_events(self):
        """主线程定时读取后台事件并刷新界面。"""
        try:
            while True:
                event = self.event_queue.get_nowait()
                if event[0] == "log":
                    self._append_log(event[2], event[1])
                elif event[0] == "done":
                    self._on_task_done(event[1], event[2], event[3])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _on_task_done(self, stats, elapsed, fatal_error):
        """恢复控件、停止进度动画并展示汇总结果。"""
        self._set_running_state(False)
        self.status_var.set(
            self.tr("status_done") if fatal_error is None else self.tr("status_failed")
        )
        summary = "\n".join([
            self.tr("sum_scanned", n=stats["scanned"]),
            self.tr("sum_moved", n=stats["moved"]),
            self.tr("sum_conflicts", n=stats["conflicts"]),
            self.tr("sum_cleaned", n=stats["cleaned"]),
            self.tr("sum_skipped", n=stats["skipped"]),
            self.tr("sum_errors", n=stats["errors"]),
            self.tr("sum_elapsed", t=elapsed),
        ])
        self._append_log(self.tr("log_summary", body=summary), "info")
        if fatal_error is None:
            messagebox.showinfo(
                "Success",
                self.tr("dlg_done_body") + "\n\n" + summary,
                parent=self.root,
            )
        else:
            messagebox.showerror(
                self.tr("dlg_fail_title"),
                self.tr("dlg_fail_body", err=fatal_error) + "\n\n" + summary,
                parent=self.root,
            )

    def _set_running_state(self, running):
        """任务运行期间禁用设置控件，防止参数被中途修改。"""
        self.is_running = running
        state = tk.DISABLED if running else tk.NORMAL
        for widget in (
            self.path_entry,
            self.browse_button,
            self.rename_check,
            self.cleanup_check,
            self.hidden_check,
            self.start_button,
            self.lang_button,
        ):
            widget.configure(state=state)
        if running:
            self.status_var.set(self.tr("status_running"))
            self.progress.start(16)
        else:
            # 停止动画并清空填充，避免空闲时残留进度色块
            self.progress.stop()

    def _append_log(self, text, level="info"):
        """向只读日志框追加内容（按级别着色），并自动滚动到最新一行。"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {text}\n", level)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_close(self):
        """任务进行中阻止直接关闭，避免后台移动过程被突然中断。"""
        if self.is_running:
            messagebox.showwarning(
                self.tr("dlg_close_title"),
                self.tr("dlg_close_body"),
                parent=self.root,
            )
            return
        # 退出前还原默认窗口过程并取消拖放注册，防止关闭时崩溃
        if self._dragdrop_restore:
            try:
                self._dragdrop_restore()
            except Exception:
                pass
            self._dragdrop_restore = None
        self.root.destroy()


def resource_path(name):
    """解析打包内嵌资源路径：PyInstaller onefile 运行时资源在 _MEIPASS 临时目录。"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def main():
    enable_windows_dpi_awareness()  # 必须在创建窗口之前开启
    root = tk.Tk()
    # 窗口标题栏与任务栏使用应用图标；图标缺失不影响运行
    icon_path = resource_path("app_icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except tk.TclError:
            pass
    FlattenFilesApp(root, scale=get_ui_scale(root))
    root.mainloop()


if __name__ == "__main__":
    main()


# PyInstaller 打包为单文件 Windows .exe 的标准终端命令（在 main.py 所在目录执行）：
# pyinstaller --noconfirm --clean --onefile --windowed --name "深层子文件夹文件一键提取平铺工具" main.py
