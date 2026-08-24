import argparse
import os
import shutil
import sys
import time
from pathlib import Path

import openai
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.utils import get_cwidth
from rich.text import Text

from . import __version__, agent, config, memory as mem, session as sess, todo, tools, undo
from .tools import _run_bash
from .ui import UI, banner, console

COMMANDS = {
    "/help": "帮助",
    "/model": "切换服务商/模型",
    "/config": "查看配置",
    "/status": "会话状态（上下文/todo/undo）",
    "/compact": "压缩上下文历史",
    "/undo": "撤销 AI 的最近一次文件修改",
    "/mem": "长期记忆 save/use/rm/list/new",
    "/resume": "恢复历史会话",
    "/safe": "开/关 外传防护（上传需批准）",
    "/clear": "清空对话并开新会话",
    "/exit": "退出",
}

MEM_SUBS = ["save", "use", "rm", "list", "new"]

HELP = """[bold]命令[/bold]（输入 / 自动补全，支持模糊匹配如 /cmp → /compact）:
  /model            选择服务商 / API key / 模型（向导）
  /model <名字>      快速切换模型（如 /model deepseek-reasoner）
  /mem              长期记忆：/mem save [标题] 存当前对话摘要
                    /mem use N 注入记忆 /mem rm N 删除 /mem list 列出 /mem new 新对话
  /config           查看当前配置
  /status           会话状态：上下文估算 / 任务清单 / undo 深度
  /compact [要求]    用 LLM 压缩历史，上下文过长时也会自动触发
  /undo             撤销 AI 最近一次文件写入/编辑（可连续撤销）
  /resume           恢复历史会话继续聊
  /safe             开/关 安全模式（断网沙盒 + 上传外发强制批准；
                    默认开，装依赖需联网时先 /safe 关）
  /clear            清空对话        /help   帮助
  /exit 或 Ctrl+D   退出            Ctrl+C  中断当前任务
  !<命令>            不经 LLM 直接跑 shell（如 !ls -la）
 启动参数: --yolo 跳过确认；交互启动时选 y 进入自主模式
 安全网: 高危命令与上传外发命令任何模式都强制二次确认
 ox alpha: 免费档上游偶发波动会自动重试；401 = key 与服务商不匹配，/model 重配"""


def _mask(k):
    if not k:
        return "[red]未设置[/red]"
    return k[:6] + "..." + k[-4:] if len(k) > 14 else "***"


# 已知 key 前缀 → 归属服务商 id / 展示名。用于拦截"把 A 家 key 填给 B 家"。
_KEY_PREFIX_HINTS = [
    ("sk-or-v1", "openrouter", "OpenRouter"),
    ("sk-or-", "openrouter", "OpenRouter"),
    ("sk-ant-", None, "Anthropic"),
    ("sk-proj-", "openai", "OpenAI 官方"),
    ("gsk_", "groq", "Groq"),
    ("AIza", "gemini", "Google Gemini"),
]


def _key_mismatch_confirm(key, pid):
    """key 前缀明显属于别家服务商时确认一下；返回 True 表示用户放弃使用。"""
    hit = next(((owner, label) for prefix, owner, label in _KEY_PREFIX_HINTS
                if key.startswith(prefix)), None)
    if hit is None or hit[0] == pid:
        return False
    console.print(
        f"[yellow]⚠ 这个 key 的格式像是 [/yellow][bold]{hit[1]}[/bold]"
        f"[yellow] 的，而不是当前服务商的。401 多半就是这么来的。[/yellow]")
    try:
        ans = console.input("[yellow]仍要使用这个 key 吗? [y/N][/yellow] "
                            ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print()
        return True
    return ans not in ("y", "yes")


def _provider_name():
    return next((pid for pid, p in config.PROVIDERS.items()
                 if p["base_url"] == config.BASE_URL), "自定义")


def new_client():
    return agent.make_client()


def _fmt_tok(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def _subseq(query, cand):
    q = query.lower()
    i = 0
    for ch in cand.lower():
        if i < len(q) and ch == q[i]:
            i += 1
    return i == len(q)


class CmdCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        parts = text.split(maxsplit=1)
        cmd = parts[0]
        if len(parts) == 2 and cmd in ("/model",):
            prefix = parts[1]
            models = [m for p in config.PROVIDERS.values()
                      for m in p["models"]]
            for m in dict.fromkeys(models):
                if _subseq(prefix, m):
                    yield Completion(m, start_position=-len(prefix),
                                     display=m)
            return
        if len(parts) == 2 and cmd in ("/mem",):
            prefix = parts[1]
            for s in MEM_SUBS:
                if _subseq(prefix, s):
                    yield Completion(s, start_position=-len(prefix),
                                     display=s)
            return
        for c, desc in COMMANDS.items():
            if len(parts) == 1 and _subseq(cmd, c) and cmd != c:
                yield Completion(c, start_position=-len(cmd),
                                 display=f"{c}  {desc}", display_meta=desc)


ACCENT_COLOR = "#4c8dff"
PANEL_BG = "#242438"
PANEL_W = 70

PT_STYLE = Style.from_dict({
    "": f"bg:{PANEL_BG}",
    "accent": f"bold {ACCENT_COLOR}",
    "prompt": "bold #e8e8e8",
    "placeholder": "#6a6a72",
    "completion-menu": "bg:#262626",
    "completion-menu.completion": "bg:#262626 fg:#aaaaaa",
    "completion-menu.completion.current": "bg:#00afff fg:#000000",
    "completion-menu.meta.completion": "bg:#262626 fg:#888888",
})


def run_task(ui, messages, user_text, state=None):
    state = state or {}
    if not messages:
        messages.append({"role": "system",
                         "content": agent.system_prompt(str(Path.cwd()))})
    messages.append({"role": "user", "content": user_text})
    t0 = time.perf_counter()

    def autosave():
        if messages:
            sess.save(state.setdefault("sid", sess.new_id()), messages,
                      {"model": config.MODEL, "base_url": config.BASE_URL,
                       "cwd": str(Path.cwd())},
                      todos=todo.items())
            todo.save(state["sid"])

    try:
        done, stats = agent.run_turn(new_client(), messages, ui,
                                     on_progress=autosave)
    except KeyboardInterrupt:
        ui.abort()
        console.print("\n[yellow]已中断当前任务[/yellow]")
        return
    except openai.AuthenticationError:
        ui.abort()
        zen = config.PROVIDERS["zen"]["base_url"] == config.BASE_URL
        console.print(
            "\n[red]✗ 401 KEY 无效或与当前服务商不匹配[/red]\n"
            f"[dim]服务商: {_provider_name()} · {config.BASE_URL}\n"
            "常见原因: 把别家的 key 填给了当前服务商 / key 过期 / 复制不全\n"
            "→ 输入 [/dim][cyan]/model[/cyan][dim] 重新配置，粘贴该服务商自己的 key"
            + ("（OpenCode Zen 免费档 key 在 opencode.ai/auth 获取）" if zen
               else "")
            + "[/dim]")
        return
    except Exception as e:
        ui.abort()
        console.print(f"\n[red]API 出错:[/red] {type(e).__name__}: {e}")
        return

    tok = agent.est_tokens(messages)
    total = time.perf_counter() - t0
    mark = "" if done else (
        "[red](模型无有效输出)[/red] " if stats.get("empty")
        else "[red](已达最大迭代)[/red] ")
    ui.status_line(
        f"{mark}{stats['turns']} 轮 · {total:.1f}s · "
        f"ctx≈{_fmt_tok(tok)} tok")

    autosave()
    state["tok"] = tok
    if done and tok > config.AUTO_COMPACT:
        console.print(
            f"[yellow]上下文已约 {_fmt_tok(tok)} tok "
            f"(阈值 {config.AUTO_COMPACT})，自动压缩历史…[/yellow]")
        do_compact(ui, messages, None, state)
        autosave()


def do_compact(ui, messages, extra, state=None):
    try:
        new = agent.compact(new_client(), messages, ui, extra)
    except KeyboardInterrupt:
        ui.abort()
        console.print("\n[yellow]压缩已取消[/yellow]")
        return
    except Exception as e:
        ui.abort()
        console.print(f"[red]压缩失败:[/red] {type(e).__name__}: {e}")
        return
    messages[:] = new
    tok = agent.est_tokens(messages)
    if state is not None:
        state["tok"] = tok
    console.print(f"[green]✓ 压缩完成[/green] "
                  f"[dim]{len(messages)} 条消息 · ctx≈{_fmt_tok(tok)} tok"
                  f"[/dim]")


def cmd_model():
    cur = next((pid for pid, p in config.PROVIDERS.items()
                if p["base_url"] == config.BASE_URL), None)
    key_state = _mask(config.API_KEY) if config.API_KEY else "[red]未设置[/red]"
    console.print(
        f"\n当前: [cyan]{config.BASE_URL}[/cyan] | "
        f"模型 [cyan]{config.MODEL}[/cyan] | KEY {key_state}\n")
    pids = list(config.PROVIDERS)
    console.print("[bold]选择服务商:[/bold]")
    for i, pid in enumerate(pids, 1):
        mark = " [green]<- 当前[/green]" if pid == cur else ""
        p = config.PROVIDERS[pid]
        console.print(f"  {i}. {p['name']}  [dim]{p['base_url']}{mark}[/dim]")
    console.print("  序号选择 · 关键词过滤(如 zen/kimi) · "
                  "或直接粘贴 OpenAI 兼容 base_url")
    try:
        choice = console.input("[bold]序号/关键词/base_url/回车取消 > [/bold]").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]已取消[/yellow]")
        return

    base_url, model, key = None, None, None
    if not choice:
        return
    if (choice and not choice.isdigit()
            and not choice.startswith(("http://", "https://"))):
        kw = choice.lower()
        hits = [(pid, p) for pid, p in config.PROVIDERS.items()
                if kw in pid or kw in p["name"].lower()]
        if not hits:
            console.print(f"[red]没有匹配 '{choice}' 的服务商[/red]")
            return
        console.print("[bold]匹配到:[/bold]")
        for i, (pid, p) in enumerate(hits, 1):
            console.print(f"  {i}. {p['name']}  [dim]{p['base_url']}[/dim]")
        try:
            raw = console.input("序号选择/回车取消 > ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]已取消[/yellow]")
            return
        if not raw.isdigit() or not (1 <= int(raw) <= len(hits)):
            console.print("[red]无效输入，已取消[/red]")
            return
        sel_pid = hits[int(raw) - 1][0]
    elif choice.isdigit() and 1 <= int(choice) <= len(pids):
        sel_pid = pids[int(choice) - 1]
    elif choice.startswith(("http://", "https://")):
        sel_pid = None
        base_url = choice.rstrip("/")
        try:
            model = console.input("模型名 > ").strip()
            if not model:
                return
            key = console.input("API Key (回车保留现有) > ").strip() or None
        except (KeyboardInterrupt, EOFError):
            console.print()
            return
        _finish_model_switch(base_url, model, key)
        return
    else:
        console.print("[red]无效输入，已取消[/red]")
        return

    p = config.PROVIDERS[sel_pid]
    base_url = p["base_url"]
    models = list(p["models"])
    if sel_pid == "ollama":
        key = "ollama"
        try:
            out = os.popen("ollama list 2>/dev/null").read()
            found = [ln.split()[0] for ln in
                     out.splitlines()[1:] if ln.strip()]
            if found:
                models = found
        except OSError:
            pass
    elif sel_pid == "lmstudio":
        key = "lmstudio"
        live = config.fetch_models(base_url, "")
        if live:
            models = live
    else:
        note = p.get("note")
        if note:
            console.print(f"[dim]ℹ {note}[/dim]")
        hint = (f"回车保留 {_mask(config.API_KEY)}"
                if config.API_KEY else "必填")
        key = console.input(f"API Key ({hint}) > ").strip() or (
            config.API_KEY or None)
        if key and _key_mismatch_confirm(key, sel_pid):
            return
        live = config.fetch_models(base_url, key or "") if key else None
        if live:
            preset = [m for m in p["models"] if m in live]
            rest = [m for m in live if m not in preset]
            models = preset + rest
            console.print(f"[green]✓ key 有效[/green] "
                          f"[dim]已在线获取 {len(live)} 个可用模型"
                          "（精选排前）[/dim]")
        elif key:
            console.print(
                "[yellow]⚠ 用该 key 在线拉取模型列表失败——可能是 key 无效、"
                "无权限或网络受限。仍将保存；若随后报 401，请确认 key 属于"
                "当前服务商（/model 可重新配置）[/yellow]")

    if not models:
        try:
            model = console.input("该服务商未预置模型，请输入模型名 > ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]已取消[/yellow]")
            return
        if not model:
            return
        _finish_model_switch(base_url, model, key)
        return

    cur_list = models
    while True:
        console.print(f"可选模型（共 {len(cur_list)} 个）:")
        for j, m in enumerate(cur_list, 1):
            tags = config.ALIAS_DISPLAY.get(m)
            tag = f"  [magenta]← {tags[0]}[/magenta]" if tags else ""
            console.print(f"  {j}. {m}{tag}")
        try:
            raw = console.input(
                f"模型名或序号 [{cur_list[0]}]（'词*' 可过滤，如 free*）> "
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]已取消[/yellow]")
            return
        if raw.endswith("*"):
            kw = raw[:-1].strip().lower()
            hits = [m for m in models if kw in m.lower()
                    or any(kw in a for a in config.ALIAS_DISPLAY.get(m, []))]
            if not hits:
                console.print(f"[red]没有匹配 '{kw}' 的模型[/red]")
                continue
            cur_list = hits
            continue
        break
    if not raw:
        model = cur_list[0]
    elif raw.isdigit() and 1 <= int(raw) <= len(cur_list):
        model = cur_list[int(raw) - 1]
    else:
        model = config.resolve_model(raw)
    _finish_model_switch(base_url, model, key)


def _finish_model_switch(base_url, model, key):
    updates_env = {"WOW_BASE_URL": base_url, "WOW_MODEL": model}
    apply_kwargs = {"base_url": base_url, "model": model}
    if key:
        updates_env["WOW_API_KEY"] = key
        apply_kwargs["key"] = key
    config.apply(**apply_kwargs)
    config.save_env(updates_env)
    console.print(f"[green]已切换并保存到 {config.ENV_FILE}[/green]: "
                  f"{base_url} | {model}")


def cmd_model_quick(model_id):
    model_id = config.resolve_model(model_id)
    config.apply(model=model_id)
    config.save_env({"WOW_MODEL": model_id})
    console.print(f"[green]模型已切换为[/green] {model_id}")


def cmd_config():
    console.print(
        f"服务商: [cyan]{_provider_name()}[/cyan]\n"
        f"BASE_URL: [cyan]{config.BASE_URL}[/cyan]\n"
        f"MODEL: [cyan]{config.MODEL}[/cyan]\n"
        f"KEY: {_mask(config.API_KEY)}\n"
        f"自动压缩阈值: {config.AUTO_COMPACT} tok\n"
        f"断网沙盒: {'开' if tools.NET_BLOCK else '关'} | "
        f"外传防护(上传需批准): {'开' if config.UPLOAD_GUARD else '关'}\n"
        f"配置文件: {config.ENV_FILE}")


def cmd_status(messages, state):
    tok = agent.est_tokens(messages)
    pct = min(100, int(tok * 100 / max(config.AUTO_COMPACT, 1)))
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    undo_n = undo.depth()
    mode = ("YOLO" if state.get("yolo")
            else "自主模式" if state.get("auto") else "命令需确认")
    console.print(
        f"会话: [cyan]{state.get('sid', '-')}[/cyan]\n"
        f"上下文: ≈[cyan]{_fmt_tok(tok)}[/cyan] tok "
        f"[dim]{bar} {pct}% of {config.AUTO_COMPACT} 自动压缩线[/dim]\n"
        f"消息数: {len(messages)} | 可撤销改动: [cyan]{undo_n}[/cyan]"
        + (f" [dim]{' '.join(undo.recent(3))}[/dim]" if undo_n else "")
        + f"\n模式: {mode} | 安全模式(沙盒+外传批准): "
        + ("开" if tools.NET_BLOCK and config.UPLOAD_GUARD else
           "关" if not tools.NET_BLOCK and not config.UPLOAD_GUARD else
           f"沙盒{'开' if tools.NET_BLOCK else '关'}/外传批准"
           f"{'开' if config.UPLOAD_GUARD else '关'}"))
    if todo.items():
        console.print(ui_todo_panel())


def ui_todo_panel():
    from .ui import render_todo_panel
    return render_todo_panel()


def cmd_mem(line, messages, state, ui):
    parts = line.split(maxsplit=2)
    sub = parts[1] if len(parts) > 1 else ""
    rows = mem.listing()

    def pick(idx_str):
        if not idx_str.isdigit() or not (1 <= int(idx_str) <= len(rows)):
            console.print("[red]序号无效[/red]，/mem 先查看列表")
            return None
        return rows[int(idx_str) - 1]

    if sub in ("", "list"):
        if not rows:
            console.print("[yellow]还没有记忆。用 /mem save [标题] 保存当前对话摘要[/yellow]")
            return
        console.print("[bold]长期记忆（任何目录可用）:[/bold]")
        for i, d in enumerate(rows, 1):
            size = len(d.get("summary", ""))
            console.print(
                f"  {i}. [cyan]{d['id']}[/cyan] [bold]{d['title']}[/bold] "
                f"[dim]{d.get('cwd', '?')} · {size} 字[/dim]")
    elif sub == "save":
        title = parts[2].strip() if len(parts) > 2 else ""
        convo = [m for m in messages
                 if m.get("role") != "system"
                 and not (m.get("content") or "").startswith("[")]
        if len(convo) < 2:
            console.print("[yellow]当前对话内容太少，没什么可存的[/yellow]")
            return
        console.print("[dim]正在压缩对话为记忆…[/dim]")
        try:
            new = agent.compact(new_client(), messages, ui, None)
        except KeyboardInterrupt:
            ui.abort()
            console.print("\n[yellow]已取消[/yellow]")
            return
        except Exception as e:
            ui.abort()
            console.print(f"[red]生成摘要失败:[/red] {type(e).__name__}: {e}")
            return
        summary = new[1]["content"]
        if not title:
            for m in convo:
                c = (m.get("content") or "").strip()
                if m.get("role") == "user" and c:
                    title = " ".join(c.split())[:24]
                    break
        mid = mem.save(summary, title=title, cwd=str(Path.cwd()),
                       model=config.MODEL)
        console.print(f"[green]✓ 记忆已保存[/green] [cyan]{mid}[/cyan] "
                      f"[dim]{title} · 任何目录 /mem use 可调用[/dim]")
    elif sub == "use":
        d = pick(parts[2].strip() if len(parts) > 2 else "")
        if d is None:
            return
        if not messages:
            messages.append({"role": "system",
                             "content": agent.system_prompt(str(Path.cwd()))})
        messages.append({
            "role": "user",
            "content": f"[长期记忆 · {d['title']}]\n{d['summary']}\n"
                       "（以上是从前的经验记忆，请结合当前任务参考）"})
        console.print(f"[green]✓ 已注入记忆[/green] [cyan]{d['title']}[/cyan]")
    elif sub == "rm":
        d = pick(parts[2].strip() if len(parts) > 2 else "")
        if d is None:
            return
        mem.delete(d["id"])
        console.print(f"[green]✓ 已删除[/green] {d['title']}")
    elif sub == "new":
        messages.clear()
        todo.reset()
        ui.set_todos([])
        state["sid"] = sess.new_id()
        state["tok"] = 0
        console.print(f"[dim]新会话 {state['sid']}（记忆仍保留，"
                      "/mem use 随时调用）[/dim]")
    else:
        console.print("[red]用法:[/red] /mem save|use|rm|list|new")


def cmd_safe():
    enable = not tools.NET_BLOCK
    tools.NET_BLOCK = enable
    config.set_upload_guard(enable)
    if enable:
        console.print("[green]✓ 安全模式已开启[/green] "
                      "[dim]shell 断网沙盒 + 上传外发命令强制批准"
                      "（装依赖需联网时先 /safe 关）[/dim]")
    else:
        console.print("[yellow]⚠ 安全模式已关闭[/yellow] "
                      "[dim]shell 可直接联网，上传外发不再强制确认，注意安全"
                      "[/dim]")


def cmd_undo():
    r = undo.undo()
    if r is None:
        console.print("[yellow]没有可撤销的文件改动了[/yellow]")
    elif r.startswith("[错误]"):
        console.print(r)
    else:
        console.print(f"[green]✓[/green] {r}")


def cmd_resume(ui, messages, state):
    rows = sess.listing()
    if not rows:
        console.print("[yellow]还没有历史会话[/yellow]")
        return
    console.print("[bold]最近的会话:[/bold]")
    for i, (sid, model, n, snippet) in enumerate(rows, 1):
        console.print(
            f"  {i}. [cyan]{sid}[/cyan] [dim]{model} · {n} 条 · "
            f"{snippet}[/dim]")
    try:
        raw = console.input("序号选择/回车取消 > ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print()
        return
    if not raw.isdigit() or not (1 <= int(raw) <= len(rows)):
        return
    d = sess.load(rows[int(raw) - 1][0])
    messages.clear()
    messages.extend(d["messages"])
    meta = d.get("meta", {})
    if meta.get("model"):
        config.apply(model=meta["model"],
                     base_url=meta.get("base_url") or None)
    state["sid"] = d["id"]
    state["tok"] = agent.est_tokens(messages)
    ui.set_todos(d.get("todos") or [])
    todo.save(d["id"])
    console.print(f"[green]✓ 已恢复会话 {d['id']}[/green] "
                  f"[dim]{len(messages)} 条消息"
                  + (f" · {todo.counts()[0]} 项任务" if todo.items() else "")
                  + "[/dim]")


def main():
    ap = argparse.ArgumentParser(prog="wow", description="wow-agent 终端编码助手")
    ap.add_argument("task", nargs="*", help="一次性任务，不给则进入交互模式")
    ap.add_argument("--yolo", action="store_true", help="跳过命令执行确认")
    ap.add_argument("-V", "--version", action="store_true")
    args = ap.parse_args()
    if args.version:
        print(f"wow-agent v{__version__}")
        return

    if not config.API_KEY:
        console.print("[yellow]首次使用，先配置服务商和 API key：[/yellow]")
        cmd_model()
        if not config.API_KEY:
            console.print("[red]仍未配置 key。可稍后在会话里用 /model 配置，"
                          "或 export WOW_API_KEY=... 后重试[/red]")
            sys.exit(1)

    ui = UI(yolo=args.yolo)
    auto = args.yolo
    state = {"sid": sess.new_id(), "tok": 0, "yolo": args.yolo, "auto": False}

    if args.task:
        run_task(ui, [], " ".join(args.task), state)
        return


    def _panel_line(txt, content_style):
        w = shutil.get_terminal_size((100, 24)).columns
        p = Text("▐", style=f"bold {ACCENT_COLOR} on {PANEL_BG}")
        p.append(f" {txt} ", style=content_style)
        pad = max(0, w - 1 - get_cwidth(f" {txt} "))
        p.append(" " * pad, style=f"on {PANEL_BG}")
        console.print(p)

    def _erase_echo(line):
        w = shutil.get_terminal_size((100, 24)).columns
        n = max(1, -(-(get_cwidth(line) + 2) // max(1, w)))
        sys.stdout.write(f"\x1b[{n}A\x1b[J")
        sys.stdout.flush()

    banner(__version__, _provider_name(), config.MODEL, str(Path.cwd()))
    _panel_line("进入自主模式？", f"bold #e8e8e8 on {PANEL_BG}")
    _panel_line("y = 免逐步确认 · 上传/高危命令仍需批准 · 实时存档"
                " · 回车 = 每步确认", f"#9a9ab0 on {PANEL_BG}")
    if not auto:
        try:
            ans = console.input("y/N > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            ans = ""
        auto = ans in ("y", "yes")
    state["auto"] = auto
    if auto:
        ui.session_allow = True
        _panel_line("自主模式已开启", f"#9a9ab0 on {PANEL_BG}")

    session = PromptSession(
        history=FileHistory(str(Path.home() / ".wow_history")),
        completer=CmdCompleter(),
        complete_while_typing=True,
        style=PT_STYLE,
    )

    messages = []

    while True:
        try:
            line = session.prompt([
                ("class:accent", "▐ "),
                ("class:prompt", ""),
            ]).strip()
        except KeyboardInterrupt:
            console.print()
            continue
        except EOFError:
            break
        if not line:
            continue
        if line == "/exit":
            break
        _erase_echo(line)
        _panel_line(line, f"#e8e8e8 on {PANEL_BG}")
        if line == "/clear":
            messages.clear()
            todo.reset()
            ui.set_todos([])
            state["sid"] = sess.new_id()
            state["tok"] = 0
            console.print("[dim]对话已清空，新会话 "
                          f"{state['sid']}[/dim]")
            continue
        if line == "/help":
            console.print(HELP)
            continue
        if line == "/config":
            cmd_config()
            continue
        if line == "/status":
            cmd_status(messages, state)
            continue
        if line == "/undo":
            cmd_undo()
            continue
        if line == "/safe":
            cmd_safe()
            continue
        if line == "/resume":
            cmd_resume(ui, messages, state)
            continue
        if line.startswith("/mem"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2 and not parts[1].strip().startswith(
                    ("save", "use", "rm", "list", "new")):
                console.print("[red]用法:[/red] /mem save|use|rm|list|new")
                continue
            cmd_mem(line, messages, state, ui)
            continue
        if line.startswith("/compact"):
            extra = line[len("/compact"):].strip() or None
            do_compact(ui, messages, extra, state)
            continue
        if line.startswith("/model"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                cmd_model_quick(parts[1].strip())
            else:
                cmd_model()
            continue
        if line.startswith("!"):
            out = _run_bash(line[1:], timeout=120)
            console.print(f"[dim]{out.strip()}[/dim]")
            continue
        if line.startswith("/"):
            console.print(f"[red]未知命令[/red] {line.split()[0]}，"
                          "输入 / 可查看补全提示")
            continue
        run_task(ui, messages, line, state)

    console.print("[dim]再见[/dim]")


if __name__ == "__main__":
    main()
