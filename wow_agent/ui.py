"""终端 UI：流式 Markdown 渲染、思考 spinner、工具卡片、彩色 diff、状态行、任务树面板。"""

import os
from contextlib import contextmanager
from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import todo

LOGO_PATH = (Path(os.environ.get("WOW_AGENT_HOME", str(Path.home())))
             / ".wow-agent" / "logo.png")

RESULT_MAX_CHARS = 600
RESULT_MAX_LINES = 18
DIFF_MAX_LINES = 40
PANEL_WIDTH = 36

_STATUS_STYLE = {
    "completed": ("✓", "green"),
    "in_progress": ("▶", "yellow"),
    "pending": ("○", "dim white"),
}
_PRIO_TAG = {
    "high": ("[H]", "red"),
    "medium": ("[M]", "yellow"),
    "low": ("[L]", "dim white"),
}
_TOOL_META = {
    "run_bash": ("$", "bash"),
    "read_file": ("›", "read"),
    "write_file": ("+", "write"),
    "edit_file": ("±", "edit"),
    "glob_files": ("*", "glob"),
    "grep_search": ("~", "grep"),
    "todo_write": ("=", "plan"),
    "task": ("@", "agent"),
}

console = Console()

_LOGO = r"""
██    ██  ██████  ██    ██
██    ██ ██    ██ ██    ██
██    ██ ██    ██ ██    ██
 ██  ██  ██    ██  ██  ██
  ████    ██████    ████
""".strip("\n")


def render_todo_panel():
    rows = todo.sorted_tree()
    total, done, prog = todo.counts()
    body = Text()
    if not rows:
        body.append("（暂无任务）", style="dim")
    for t, depth in rows:
        icon, color = _STATUS_STYLE[t["status"]]
        tag, tag_color = _PRIO_TAG[t["priority"]]
        pad = "  " * depth
        body.append(f"{pad}{icon} ", style=color)
        body.append(tag, style=tag_color)
        content_style = "dim strikethrough" if t["status"] == "completed" else ""
        body.append(f" {t['content']}\n",
                    style=color if t["status"] == "in_progress" else content_style)
        if t["note"]:
            note = " ".join(t["note"].split())
            if len(note) > 46:
                note = note[:46] + "…"
            body.append(f"{pad}   └ {note}\n", style="dim italic")
    title = f"☰ 计划 {done}/{total}" + (f" · ▶{prog}" if prog else "")
    return Panel(body, title=title, title_align="left",
                 border_style="magenta", width=PANEL_WIDTH)


def image_art(path, max_cols=46):
    """像素画转终端块字符：抠图去底、去掉下方文字段、双色硬边。"""
    from PIL import Image, ImageChops, ImageFilter

    img = Image.open(path).convert("RGB")
    bg = img.getpixel((2, 2))
    W, H = img.size
    diff = ImageChops.difference(img, Image.new("RGB", img.size, bg))
    mask = diff.convert("L").point(lambda v: 255 if v > 26 else 0)
    try:
        mask = mask.filter(ImageFilter.MedianFilter(5))
    except Exception:
        pass

    rp = mask.resize((1, H), Image.BOX).load()
    row_on = [rp[0, y] > 6 for y in range(H)]
    segs = []
    start = None
    for y in range(H):
        if row_on[y] and start is None:
            start = y
        elif not row_on[y] and start is not None:
            segs.append([start, y])
            start = None
    if start is not None:
        segs.append([start, H])
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < H // 50:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    if merged:
        top = max(merged, key=lambda s: s[1] - s[0])
        img = img.crop((0, top[0], W, top[1]))
        diff = diff.crop((0, top[0], W, top[1]))

    bbox = diff.convert("L").point(lambda v: 255 if v > 26 else 0).getbbox()
    if not bbox:
        bbox = (0, 0, W, H)
    pad = max(2, min(W, H) // 80)
    bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
            min(W, bbox[2] + pad), min(H, bbox[3] + pad))
    img = img.crop(bbox)

    def dist2(p, q):
        return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2

    w, h = img.size
    cols = max(8, min(max_cols, w))
    rows = max(2, round(cols * h / w / 2))
    small = img.resize((cols, rows * 2), Image.NEAREST)
    px = small.load()

    fg_sum = [0, 0, 0]
    fg_n = 0
    grid = []
    for y in range(rows * 2):
        row = []
        for x in range(cols):
            p = px[x, y]
            on = dist2(p, bg) > 3600
            row.append(on)
            if on:
                fg_sum[0] += p[0]
                fg_sum[1] += p[1]
                fg_sum[2] += p[2]
                fg_n += 1
        grid.append(row)
    fg = (tuple(c // max(1, fg_n) for c in fg_sum)) if fg_n else (200, 200, 200)
    fg_s = f"rgb({fg[0]},{fg[1]},{fg[2]})"

    col_on = [any(grid[y][x] for y in range(rows * 2)) for x in range(cols)]
    row_on = [any(grid[y][x] for x in range(cols)) for y in range(rows * 2)]
    xs = [x for x in range(cols) if col_on[x]]
    ys = [y for y in range(rows * 2) if row_on[y]]
    if xs and ys:
        x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
    else:
        x0, x1, y0, y1 = 0, cols - 1, 0, rows * 2 - 1

    lines = []
    for y in range(y0, y1 + 1, 2):
        t = Text()
        for x in range(x0, x1 + 1):
            top = grid[y][x]
            bot = grid[min(y + 1, rows * 2 - 1)][x]
            if top and bot:
                t.append("█", style=fg_s)
            elif top:
                t.append("▀", style=fg_s)
            elif bot:
                t.append("▄", style=fg_s)
            else:
                t.append(" ")
        lines.append(t)
    return Group(*lines)


def banner(version, provider, model, cwd=""):
    console.print()
    shown = False
    if LOGO_PATH.exists() and console.width >= 46:
        try:
            art = image_art(LOGO_PATH, max_cols=44)
            for line in art.renderables:
                console.print(line, justify="center")
            shown = True
        except Exception:
            shown = False
    if not shown:
        console.print(Text(_LOGO, style="bold #4c8dff"), justify="center")
    console.print()
    tip = Text()
    tip.append("● ", style="#e5a50a")
    tip.append("Tip ", style="bold #e5a50a")
    tip.append("/undo 撤销最近修改 · /help 全部命令", style="#8a8a92")
    console.print(tip, justify="center")
    w = console.width
    left = Text(f" {cwd}", style="dim")
    right = Text(f"wow-agent v{version} ", style="dim")
    pad = max(1, w - left.cell_len - right.cell_len)
    row = Text()
    row.append_text(left)
    row.append(" " * pad)
    row.append_text(right)
    console.print(row)


class UI:
    def __init__(self, yolo=False, out=None):
        self.yolo = yolo
        self.session_allow = False
        self.console = out or console
        self._live = None
        self._buf = []
        self._think = None

    # ---------- 任务树面板 ----------
    def todo_renderable(self):
        return render_todo_panel()

    def set_todos(self, items):
        todo.set_all(items)
        self._refresh_frame()
        if self._live is None and todo.items():
            self.console.print(self.todo_renderable())

    def todo_badge(self):
        total, done, prog = todo.counts()
        return f"☑{done}/{total}" if total else ""

    def _frame(self):
        md = Markdown("".join(self._buf))
        if not todo.items():
            return md
        if self.console.width < PANEL_WIDTH + 40:
            return Group(self.todo_renderable(), md)
        grid = Table.grid(padding=(0, 1))
        grid.add_column(width=PANEL_WIDTH, vertical="top")
        grid.add_column(ratio=1, vertical="top")
        grid.add_row(render_todo_panel(), md)
        return grid

    def _refresh_frame(self):
        if self._live is not None:
            self._live.update(self._frame())

    # ---------- 流式文本 ----------
    def text_begin(self):
        self._live = None
        self._buf = []

    def text_delta(self, s):
        if self._live is None:
            # transient=True：Live 停止时擦掉自己画的全部帧，
            # 这样流式中途断线重试时半截输出不会残留在屏幕上
            self._live = Live(console=self.console, refresh_per_second=12,
                              vertical_overflow="visible", transient=True)
            self._live.start()
        self._buf.append(s)
        self._refresh_frame()

    def text_end(self):
        if self._live is not None:
            self._live.stop()
            self._live = None
        if self._buf:
            self.console.print(Markdown("".join(self._buf)))
        self._buf = []

    def text_discard(self):
        """丢弃未完成的流式输出（上游断线/空回复重试时用），不留残留。"""
        if self._live is not None:
            self._live.stop()
            self._live = None
        self._buf = []

    def abort(self):
        self.think_end()
        self.text_end()

    # ---------- 思考 spinner ----------
    def think_begin(self, label="思考中"):
        self.think_end()
        try:
            self._think = self.console.status(
                f"[cyan]{label}…[/cyan]", spinner="dots")
            self._think.start()
        except Exception:
            self._think = None

    def think_end(self):
        if self._think is not None:
            try:
                self._think.stop()
            except Exception:
                pass
            self._think = None

    def think_update(self, label):
        if self._think is not None:
            try:
                self._think.update(f"[cyan]{label}…[/cyan]")
            except Exception:
                pass

    # ---------- 工具卡片 ----------
    def tool_start(self, name, args_str):
        label = _TOOL_META.get(name, (None, name))[1].capitalize()
        preview = " ".join(args_str.split())[:90]
        self.console.print(
            f"[bold #4c8dff]▪[/bold #4c8dff] [bold]{label}[/bold]"
            f"([dim]{preview}[/dim])")

    def tool_result(self, name, result, elapsed):
        err = result.lstrip().startswith(
            ("[错误]", "[工具执行出错]", "[用户拒绝"))
        color = "red" if err else "dim"
        body = result.strip()
        lines = body.splitlines()
        cut = ""
        if len(lines) > RESULT_MAX_LINES:
            lines = lines[:RESULT_MAX_LINES]
            cut = f"\n  … [已截断，共 {len(body)} 字符]"
        elif len(body) > RESULT_MAX_CHARS:
            lines = body[:RESULT_MAX_CHARS].splitlines()
            cut = f"\n  … [已截断，共 {len(result)} 字符]"
        shown = "\n".join("  " + ln for ln in lines)
        self.console.print(Text(shown + cut, style=color))

    def diff(self, diff_lines, is_new=False):
        if not diff_lines:
            return
        shown = diff_lines[:DIFF_MAX_LINES]
        for ln in shown:
            if ln.startswith(("+++", "---")):
                self.console.print(f"  [bold]{ln}[/bold]")
            elif ln.startswith("@@"):
                self.console.print(f"  [cyan]{ln}[/cyan]")
            elif ln.startswith("+"):
                self.console.print(f"  [green]{ln}[/green]")
            elif ln.startswith("-"):
                self.console.print(f"  [red]{ln}[/red]")
            else:
                self.console.print(f"  [dim]{ln}[/dim]")
        if len(diff_lines) > DIFF_MAX_LINES:
            self.console.print(
                f"  [dim]… 共 {len(diff_lines)} 行差异[/dim]")

    # ---------- 确认 ----------
    def confirm(self, command, force=False):
        if not force and (self.yolo or self.session_allow):
            return True
        try:
            ans = self.console.input(
                f"[yellow]>> 执行? [/yellow]{command} "
                f"[yellow][y/N/a=本会话全允许][/] ")
        except (KeyboardInterrupt, EOFError):
            self.console.print()
            return False
        a = ans.strip().lower()
        if a in ("a", "all") and not force:
            self.session_allow = True
            self.console.print("[dim]本会话后续命令将自动执行"
                               "（高危命令仍会询问）[/dim]")
            return True
        return a in ("y", "yes")

    # ---------- 状态行 ----------
    def status_line(self, text):
        from . import __version__
        w = self.console.width
        cwd = str(Path.cwd())
        home = str(Path.home())
        cwd = "~" + cwd[len(home):] if cwd.startswith(home) else cwd
        left = Text(f" {cwd}", style="dim")
        mid = Text(f"▪ {text} ", style="#8a8a92")
        right = Text(f"wow-agent v{__version__} ", style="dim")
        pad = max(1, w - left.cell_len - mid.cell_len - right.cell_len)
        row = Text()
        row.append_text(left)
        row.append(" " * (pad // 2))
        row.append_text(mid)
        row.append(" " * (pad - pad // 2))
        row.append_text(right)
        self.console.print(row)

    @contextmanager
    def capture(self):
        """测试用：静音输出。"""
        yield self
