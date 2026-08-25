# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

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

from . import (__version__, agent, config, i18n, memory as mem,
               session as sess, subagent, todo, tools, undo)
from .i18n import tr
from .tools import _run_bash
from .ui import UI, banner, console


def command_descriptions():
    return {
        "/help": tr("帮助", "Help"),
        "/model": tr("切换服务商/模型", "Switch provider/model"),
        "/config": tr("查看配置", "Show config"),
        "/status": tr("会话状态（上下文/todo/undo）",
                      "Session status (context/todo/undo)"),
        "/compact": tr("压缩上下文历史", "Compact context history"),
        "/undo": tr("撤销 AI 的最近一次文件修改",
                    "Undo last AI file change"),
        "/mem": tr("长期记忆 save/use/rm/list/new",
                   "Long-term memory save/use/rm/list/new"),
        "/resume": tr("恢复历史会话", "Resume a session"),
        "/review": tr("只读代码审查（🔴高风险/🟡建议/🟢优化）",
                      "Read-only code review"),
        "/language": tr("切换语言 en|zh（默认英文）",
                        "Switch language en|zh (default English)"),
        "/safe": tr("开/关 外传防护（上传需批准）",
                    "Toggle safe mode (uploads need approval)"),
        "/clear": tr("清空对话并开新会话", "Clear conversation"),
        "/exit": tr("退出", "Exit"),
    }


COMMANDS = command_descriptions()

MEM_SUBS = ["save", "use", "rm", "list", "new"]


def review_system():
    return tr(
        "你是 wow-agent 的只读代码审查子代理，在干净上下文里调研，"
        "不执行任何修改。\n"
        "- 只用 read_file / glob_files / grep_search / 查看类 bash 命令\n"
        "- 审查重点：安全风险（注入/密钥泄漏/越权）、正确性（边界/错误处理/"
        "资源泄漏）、设计与性能；小问题不必穷举，挑值得改的说\n"
        f"- 最多 {config.SUB_ITER} 轮调研\n"
        "- 最后一条回复输出审查报告，严格分三节：\n"
        "🔴 高风险\n🟡 建议\n🟢 优化\n"
        "每条格式 `- 路径:行号 · 问题 · 修复建议`；某节没有就写（无），"
        "不要客套话",
        "You are wow-agent's read-only code review subagent. Research in a "
        "clean context; never modify anything.\n"
        "- Only use read_file / glob_files / grep_search / read-only bash\n"
        "- Focus on: security (injection/secrets/privileges), correctness "
        "(edge cases/error handling/resource leaks), design & performance; "
        "skip trivia, report what matters\n"
        f"- At most {config.SUB_ITER} research turns\n"
        "- Final reply is the review report, strictly three sections:\n"
        "🔴 High risk\n🟡 Suggestions\n🟢 Optimizations\n"
        "Each item: `- path:line · issue · fix`; write (none) for empty "
        "sections; no fluff")


HELP_ZH = """[bold]命令[/bold]（输入 / 自动补全，支持模糊匹配如 /cmp → /compact）:
  /model            选择服务商 / API key / 模型（向导）
  /model <名字>      快速切换模型（如 /model deepseek-reasoner）
  /mem              长期记忆：/mem save [标题] 存当前对话摘要
                    /mem use N 注入记忆 /mem rm N 删除 /mem list 列出 /mem new 新对话
  /config           查看当前配置
  /status           会话状态：上下文估算 / 任务清单 / undo 深度
  /compact [要求]    用 LLM 压缩历史，上下文过长时也会自动触发
  /undo             撤销 AI 最近一次文件写入/编辑（可连续撤销；任务失败可整轮回滚）
  /resume           恢复历史会话继续聊
  /review [路径]     只读代码审查：🔴高风险 / 🟡建议 / 🟢优化 三级报告
  /language         切换中英文（/language en|zh，默认英文）
  /safe             开/关 安全模式（断网沙盒 + 上传外发强制批准；
                    默认开，装依赖需联网时先 /safe 关）
  /clear            清空对话        /help   帮助
  /exit 或 Ctrl+D   退出            Ctrl+C  中断当前任务
  !<命令>            不经 LLM 直接跑 shell（如 !ls -la）
 启动参数: --yolo 跳过确认；交互启动时选 y 进入自主模式
 安全网: 高危命令与上传外发命令任何模式都强制二次确认
 ox alpha: 免费档上游偶发波动会自动重试；401 = key 与服务商不匹配，/model 重配"""

HELP_EN = """[bold]Commands[/bold] (type / to autocomplete, fuzzy match like /cmp -> /compact):
  /model            Pick provider / API key / model (wizard)
  /model <name>     Quick switch model (e.g. /model deepseek-reasoner)
  /mem              Long-term memory: /mem save [title] store summary
                    /mem use N inject /mem rm N delete /mem list /mem new
  /config           Show current config
  /status           Session status: context / todo tree / undo depth
  /compact [hint]   LLM-compact history (also auto-triggered when long)
  /undo             Undo last AI write/edit (repeatable; failed turns roll back)
  /resume           Resume a previous session
  /review [path]    Read-only review: 🔴 high risk / 🟡 suggest / 🟢 optimize
  /language         Switch language (/language en|zh, default English)
  /safe             Toggle safe mode (network sandbox + upload approval;
                    on by default, /safe off when installing deps)
  /clear            Clear conversation        /help   help
  /exit or Ctrl+D   quit                     Ctrl+C  interrupt task
  !<cmd>            Run shell directly without LLM (e.g. !ls -la)
 Startup: --yolo skips confirmations; pick y at launch for auto mode
 Safety: dangerous & upload commands always require confirmation
 ox alpha: free-tier flakiness auto-retries; 401 = wrong key, /model to fix"""


def help_text():
    return tr(HELP_ZH, HELP_EN)


def _mask(k):
    if not k:
        return tr("[red]未设置[/red]", "[red]not set[/red]")
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
        for c, desc in command_descriptions().items():
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
        console.print("\n[yellow]"
                      + tr("已中断当前任务", "Task interrupted") + "[/yellow]")
        return
    except openai.AuthenticationError:
        ui.abort()
        zen = config.PROVIDERS["zen"]["base_url"] == config.BASE_URL
        console.print(
            "\n[red]"
            + tr("✗ 401 KEY 无效或与当前服务商不匹配",
                 "✗ 401 key invalid or mismatched with this provider")
            + "[/red]\n"
            + f"[dim]{tr('服务商', 'Provider')}: {_provider_name()} · "
              f"{config.BASE_URL}\n"
            + tr("常见原因: 把别家的 key 填给了当前服务商 / key 过期 / 复制不全\n"
                 "→ 输入 ",
                 "Common causes: key from another provider / expired / "
                 "truncated\n→ type ")
            + "[/dim][cyan]/model[/cyan][dim]"
            + tr(" 重新配置，粘贴该服务商自己的 key",
                 " to reconfigure with that provider's own key")
            + (tr("（OpenCode Zen 免费档 key 在 opencode.ai/auth 获取）",
                  " (free Zen key at opencode.ai/auth)") if zen else "")
            + "[/dim]")
        return
    except Exception as e:
        ui.abort()
        console.print(f"\n[red]{tr('API 出错', 'API error')}:[/red] "
                      f"{type(e).__name__}: {e}")
        return

    if not done and stats.get("cid"):
        n = undo.group_depth(stats["cid"])
        if n and ui.confirm(
                tr(f"[red]本轮未正常完成[/red] 回滚本轮 AI 的 {n} 处文件改动?",
                   f"[red]Turn did not finish[/red] roll back all {n} AI "
                   "file changes this turn?"),
                force=True):
            for m in undo.undo_group(stats["cid"]):
                if m.startswith("[错误]"):
                    console.print(f"  [red]{m}[/red]")
                else:
                    console.print(f"  [green]✓[/green] {m}")

    tok = agent.est_tokens(messages)
    total = time.perf_counter() - t0
    mark = "" if done else (
        tr("[red](模型无有效输出)[/red] ", "[red](no valid output)[/red] ")
        if stats.get("empty")
        else tr("[red](已达最大迭代)[/red] ",
                "[red](max iterations reached)[/red] "))
    ui.status_line(
        f"{mark}{stats['turns']} {tr('轮', 'turns')} · {total:.1f}s · "
        f"ctx≈{_fmt_tok(tok)} tok")

    autosave()
    state["tok"] = tok
    if done and tok > config.AUTO_COMPACT:
        console.print(
            tr(f"[yellow]上下文已约 {_fmt_tok(tok)} tok "
               f"(阈值 {config.AUTO_COMPACT})，自动压缩历史…[/yellow]",
               f"[yellow]Context ≈ {_fmt_tok(tok)} tok "
               f"(threshold {config.AUTO_COMPACT}), auto-compacting…"
               "[/yellow]"))
        do_compact(ui, messages, None, state)
        autosave()


def do_compact(ui, messages, extra, state=None):
    try:
        new = agent.compact(new_client(), messages, ui, extra)
    except KeyboardInterrupt:
        ui.abort()
        console.print("\n[yellow]"
                      + tr("压缩已取消", "Compact cancelled") + "[/yellow]")
        return
    except Exception as e:
        ui.abort()
        console.print(f"[red]{tr('压缩失败', 'Compact failed')}:[/red] "
                      f"{type(e).__name__}: {e}")
        return
    messages[:] = new
    tok = agent.est_tokens(messages)
    if state is not None:
        state["tok"] = tok
    console.print(
        f"[green]✓ {tr('压缩完成', 'Compacted')}[/green] "
        f"[dim]{len(messages)} {tr('条消息', 'messages')} · "
        f"ctx≈{_fmt_tok(tok)} tok[/dim]")


def cmd_model():
    cur = next((pid for pid, p in config.PROVIDERS.items()
                if p["base_url"] == config.BASE_URL), None)
    key_state = _mask(config.API_KEY) if config.API_KEY else "[red]未设置[/red]"
    console.print(
        f"\n{tr('当前', 'Current')}: [cyan]{config.BASE_URL}[/cyan] | "
        f"{tr('模型', 'Model')} [cyan]{config.MODEL}[/cyan] | KEY {key_state}\n")
    pids = list(config.PROVIDERS)
    console.print(f"[bold]{tr('选择服务商', 'Choose a provider')}:[/bold]")
    for i, pid in enumerate(pids, 1):
        mark = (f" [green]<- {tr('当前', 'current')}[/green]"
                if pid == cur else "")
        p = config.PROVIDERS[pid]
        console.print(f"  {i}. {p['name']}  [dim]{p['base_url']}{mark}[/dim]")
    console.print("  "
                  + tr("序号选择 · 关键词过滤(如 zen/kimi) · "
                       "或直接粘贴 OpenAI 兼容 base_url",
                       "Pick by number · keyword filter (zen/kimi) · "
                       "or paste an OpenAI-compatible base_url"))
    try:
        choice = console.input(
            tr("序号/关键词/base_url/回车取消 > ",
               "number/keyword/base_url/enter to cancel > ")).strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]" + tr("已取消", "Cancelled") + "[/yellow]")
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
            console.print(f"[red]{tr('没有匹配', 'No provider matches')} "
                          f"'{choice}'[/red]")
            return
        console.print(f"[bold]{tr('匹配到', 'Matches')}:[/bold]")
        for i, (pid, p) in enumerate(hits, 1):
            console.print(f"  {i}. {p['name']}  [dim]{p['base_url']}[/dim]")
        try:
            raw = console.input(
                tr("序号选择/回车取消 > ", "number/enter to cancel > ")
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]" + tr("已取消", "Cancelled") + "[/yellow]")
            return
        if not raw.isdigit() or not (1 <= int(raw) <= len(hits)):
            console.print("[red]" + tr("无效输入，已取消",
                                       "Invalid input, cancelled") + "[/red]")
            return
        sel_pid = hits[int(raw) - 1][0]
    elif choice.isdigit() and 1 <= int(choice) <= len(pids):
        sel_pid = pids[int(choice) - 1]
    elif choice.startswith(("http://", "https://")):
        sel_pid = None
        base_url = choice.rstrip("/")
        try:
            model = console.input(
                tr("模型名 > ", "Model name > ")).strip()
            if not model:
                return
            key = console.input(
                tr("API Key (回车保留现有) > ",
                   "API Key (enter to keep current) > ")).strip() or None
        except (KeyboardInterrupt, EOFError):
            console.print()
            return
        _finish_model_switch(base_url, model, key)
        return
    else:
        console.print("[red]" + tr("无效输入，已取消",
                                   "Invalid input, cancelled") + "[/red]")
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
        hint = (tr(f"回车保留 {_mask(config.API_KEY)}",
                   f"enter to keep {_mask(config.API_KEY)}")
                if config.API_KEY else tr("必填", "required"))
        key = console.input(f"API Key ({hint}) > ").strip() or (
            config.API_KEY or None)
        if key and _key_mismatch_confirm(key, sel_pid):
            return
        live = config.fetch_models(base_url, key or "") if key else None
        if live:
            preset = [m for m in p["models"] if m in live]
            rest = [m for m in live if m not in preset]
            models = preset + rest
            console.print(
                f"[green]✓ {tr('key 有效', 'key valid')}[/green] "
                f"[dim]{tr('已在线获取', 'fetched')} {len(live)} "
                + tr("个可用模型（精选排前）",
                     "models online (curated first)") + "[/dim]")
        elif key:
            console.print(
                tr("[yellow]⚠ 用该 key 在线拉取模型列表失败——可能是 key 无效、"
                   "无权限或网络受限。仍将保存；若随后报 401，请确认 key 属于"
                   "当前服务商（/model 可重新配置）[/yellow]",
                   "[yellow]⚠ Failed to fetch model list with this key — "
                   "it may be invalid, unauthorized, or the network is "
                   "restricted. Saving anyway; if you then get 401, check "
                   "the key belongs to this provider (/model to "
                   "reconfigure)[/yellow]"))

    if not models:
        try:
            model = console.input(
                tr("该服务商未预置模型，请输入模型名 > ",
                   "No preset models for this provider, enter model name > ")
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]" + tr("已取消", "Cancelled") + "[/yellow]")
            return
        if not model:
            return
        _finish_model_switch(base_url, model, key)
        return

    cur_list = models
    while True:
        console.print(f"{tr('可选模型（共', 'Models (')}"
                      f" {len(cur_list)} {tr('个）', ')}')}:")
        for j, m in enumerate(cur_list, 1):
            tags = config.ALIAS_DISPLAY.get(m)
            tag = f"  [magenta]← {tags[0]}[/magenta]" if tags else ""
            console.print(f"  {j}. {m}{tag}")
        try:
            raw = console.input(
                tr(f"模型名或序号 [{cur_list[0]}]（'词*' 可过滤，如 free*）> ",
                   f"model name or number [{cur_list[0]}] ('kw*' filters, "
                   "e.g. free*) > ")
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]" + tr("已取消", "Cancelled") + "[/yellow]")
            return
        if raw.endswith("*"):
            kw = raw[:-1].strip().lower()
            hits = [m for m in models if kw in m.lower()
                    or any(kw in a for a in config.ALIAS_DISPLAY.get(m, []))]
            if not hits:
                console.print(f"[red]{tr('没有匹配', 'No model matches')} "
                              f"'{kw}'[/red]")
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
    console.print(f"[green]{tr('已切换并保存到', 'Switched and saved to')} "
                  f"{config.ENV_FILE}[/green]: {base_url} | {model}")


def cmd_model_quick(model_id):
    model_id = config.resolve_model(model_id)
    config.apply(model=model_id)
    config.save_env({"WOW_MODEL": model_id})
    console.print(f"[green]{tr('模型已切换为', 'Model switched to')}[/green] "
                  f"{model_id}")


def cmd_config():
    try:
        from . import mcp
        mcp_n = (f"{len(mcp.status())} "
                 + tr("个", "") + f" ({mcp.CONF})")
    except Exception:
        mcp_n = f"0 {tr('个', '')}"
    console.print(
        f"{tr('服务商', 'Provider')}: [cyan]{_provider_name()}[/cyan]\n"
        f"BASE_URL: [cyan]{config.BASE_URL}[/cyan]\n"
        f"MODEL: [cyan]{config.MODEL}[/cyan]\n"
        f"KEY: {_mask(config.API_KEY)}\n"
        + tr(f"自动压缩阈值: {config.AUTO_COMPACT} tok\n",
             f"Auto-compact threshold: {config.AUTO_COMPACT} tok\n")
        + tr(f"断网沙盒: {'开' if tools.NET_BLOCK else '关'} | ",
             f"Network sandbox: {'on' if tools.NET_BLOCK else 'off'} | ")
        + tr(f"外传防护(上传需批准): {'开' if config.UPLOAD_GUARD else '关'}\n",
             f"Upload guard (approve uploads): "
             f"{'on' if config.UPLOAD_GUARD else 'off'}\n")
        + tr(f"MCP servers: {mcp_n}\n", f"MCP servers: {mcp_n}\n")
        + tr(f"语言: {i18n.LANG}\n", f"Language: {i18n.LANG}\n")
        + tr(f"配置文件: {config.ENV_FILE}", f"Config file: {config.ENV_FILE}"))


def cmd_status(messages, state):
    tok = agent.est_tokens(messages)
    pct = min(100, int(tok * 100 / max(config.AUTO_COMPACT, 1)))
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    undo_n = undo.depth()
    mode = ("YOLO" if state.get("yolo")
            else tr("自主模式", "auto mode") if state.get("auto")
            else tr("命令需确认", "confirm each command"))
    ph = todo.PHASE_LABEL.get(todo.phase(), "")
    console.print(
        f"{tr('会话', 'Session')}: [cyan]{state.get('sid', '-')}[/cyan]\n"
        + tr(f"上下文: ≈[cyan]{_fmt_tok(tok)}[/cyan] tok ",
             f"Context: ≈[cyan]{_fmt_tok(tok)}[/cyan] tok ")
        + f"[dim]{bar} {pct}% of {config.AUTO_COMPACT} "
        + tr("自动压缩线", "auto-compact line") + "[/dim]\n"
        + tr(f"消息数: {len(messages)} | 可撤销改动: [cyan]{undo_n}[/cyan]",
             f"Messages: {len(messages)} | Undoable changes: "
             f"[cyan]{undo_n}[/cyan]")
        + (f" [dim]{' '.join(undo.recent(3))}[/dim]" if undo_n else "")
        + "\n" + tr(f"任务阶段: {ph} | 模式: {mode} | 安全模式(沙盒+外传批准): ",
                    f"Task phase: {ph} | Mode: {mode} | Safe mode "
                    "(sandbox+upload approval): ")
        + (tr("开", "on") if tools.NET_BLOCK and config.UPLOAD_GUARD else
           tr("关", "off") if not tools.NET_BLOCK and not config.UPLOAD_GUARD
           else tr(f"沙盒{'开' if tools.NET_BLOCK else '关'}/外传批准"
                   f"{'开' if config.UPLOAD_GUARD else '关'}",
                   f"sandbox {'on' if tools.NET_BLOCK else 'off'}/upload "
                   f"guard {'on' if config.UPLOAD_GUARD else 'off'}")))
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
            console.print(f"[red]{tr('序号无效', 'Invalid number')}[/red]，"
                          + tr("/mem 先查看列表", "list with /mem first"))
            return None
        return rows[int(idx_str) - 1]

    if sub in ("", "list"):
        if not rows:
            console.print(tr(
                "[yellow]还没有记忆。用 /mem save [标题] 保存当前对话摘要[/yellow]",
                "[yellow]No memories yet. /mem save [title] to store a "
                "summary of this conversation[/yellow]"))
            return
        console.print(tr("[bold]长期记忆（任何目录可用）:[/bold]",
                         "[bold]Long-term memory (works in any directory):"
                         "[/bold]"))
        for i, d in enumerate(rows, 1):
            size = len(d.get("summary", ""))
            console.print(
                f"  {i}. [cyan]{d['id']}[/cyan] [bold]{d['title']}[/bold] "
                f"[dim]{d.get('cwd', '?')} · {size} "
                + tr("字", "chars") + "[/dim]")
    elif sub == "save":
        title = parts[2].strip() if len(parts) > 2 else ""
        convo = [m for m in messages
                 if m.get("role") != "system"
                 and not (m.get("content") or "").startswith("[")]
        if len(convo) < 2:
            console.print(tr("[yellow]当前对话内容太少，没什么可存的[/yellow]",
                             "[yellow]Not enough conversation to store"
                             "[/yellow]"))
            return
        console.print(tr("[dim]正在压缩对话为记忆…[/dim]",
                         "[dim]Compacting conversation into memory…[/dim]"))
        try:
            new = agent.compact(new_client(), messages, ui, None)
        except KeyboardInterrupt:
            ui.abort()
            console.print("\n[yellow]" + tr("已取消", "Cancelled") + "[/yellow]")
            return
        except Exception as e:
            ui.abort()
            console.print(f"[red]{tr('生成摘要失败', 'Summary failed')}:"
                          f"[/red] {type(e).__name__}: {e}")
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
        dup = mem.find_title(title)
        if dup and dup["id"] != mid:
            mem.delete(dup["id"])
        pruned = mem.enforce_cap()
        note = ""
        if dup and dup["id"] != mid:
            note = tr(" · 同名旧记忆已更新",
                      " · same-title memory updated")
        if pruned:
            note += tr(f" · 超 {mem.MAX_MEMS} 条已自动清理最旧 {pruned} 条",
                       f" · over {mem.MAX_MEMS}, pruned {pruned} oldest")
        console.print(f"[green]✓ {tr('记忆已保存', 'Memory saved')}[/green] "
                      f"[cyan]{mid}[/cyan] "
                      f"[dim]{title}{note} · "
                      + tr("任何目录 /mem use 可调用",
                           "/mem use it from any directory") + "[/dim]")
    elif sub == "use":
        d = pick(parts[2].strip() if len(parts) > 2 else "")
        if d is None:
            return
        if not messages:
            messages.append({"role": "system",
                             "content": agent.system_prompt(str(Path.cwd()))})
        messages.append({
            "role": "user",
            "content": tr(f"[长期记忆 · {d['title']}]\n{d['summary']}\n"
                          "（以上是从前的经验记忆，请结合当前任务参考）",
                          f"[Long-term memory · {d['title']}]\n{d['summary']}"
                          "\n(Past experience; use it together with the "
                          "current task)")})
        console.print(f"[green]✓ {tr('已注入记忆', 'Memory injected')}"
                      f"[/green] [cyan]{d['title']}[/cyan]")
    elif sub == "rm":
        d = pick(parts[2].strip() if len(parts) > 2 else "")
        if d is None:
            return
        mem.delete(d["id"])
        console.print(f"[green]✓ {tr('已删除', 'Deleted')}[/green] "
                      f"{d['title']}")
    elif sub == "new":
        messages.clear()
        todo.reset()
        ui.set_todos([])
        state["sid"] = sess.new_id()
        state["tok"] = 0
        console.print(f"[dim]{tr('新会话', 'New session')} {state['sid']}"
                      + tr("（记忆仍保留，/mem use 随时调用）",
                           " (memories kept, /mem use anytime)") + "[/dim]")
    else:
        console.print(f"[red]{tr('用法', 'Usage')}:[/red] "
                      "/mem save|use|rm|list|new")


def cmd_safe():
    enable = not tools.NET_BLOCK
    tools.NET_BLOCK = enable
    config.set_upload_guard(enable)
    if enable:
        console.print(f"[green]✓ {tr('安全模式已开启', 'Safe mode ON')}[/green] "
                      "[dim]"
                      + tr("shell 断网沙盒 + 上传外发命令强制批准"
                           "（装依赖需联网时先 /safe 关）",
                           "shell network sandbox + uploads need approval "
                           "(/safe off when installing deps)") + "[/dim]")
    else:
        console.print(f"[yellow]⚠ {tr('安全模式已关闭', 'Safe mode OFF')}"
                      "[/yellow] [dim]"
                      + tr("shell 可直接联网，上传外发不再强制确认，注意安全",
                           "shell has direct network; uploads no longer "
                           "confirmed. Be careful.") + "[/dim]")


def cmd_undo():
    r = undo.undo()
    if r is None:
        console.print(tr("[yellow]没有可撤销的文件改动了[/yellow]",
                         "[yellow]Nothing to undo[/yellow]"))
    elif r.startswith("[错误]"):
        console.print(r)
    else:
        console.print(f"[green]✓[/green] {r}")


def cmd_resume(ui, messages, state):
    rows = sess.listing()
    if not rows:
        console.print(tr("[yellow]还没有历史会话[/yellow]",
                         "[yellow]No previous sessions[/yellow]"))
        return
    console.print(tr("[bold]最近的会话:[/bold]", "[bold]Recent sessions:"
                                             "[/bold]"))
    for i, (sid, model, n, snippet) in enumerate(rows, 1):
        console.print(
            f"  {i}. [cyan]{sid}[/cyan] [dim]{model} · {n} "
            + tr("条", "msgs") + f" · {snippet}[/dim]")
    try:
        raw = console.input(
            tr("序号选择/回车取消 > ", "number/enter to cancel > ")).strip()
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
    console.print(f"[green]✓ {tr('已恢复会话', 'Resumed session')} "
                  f"{d['id']}[/green] "
                  f"[dim]{len(messages)} {tr('条消息', 'messages')}"
                  + (f" · {todo.counts()[0]} " + tr("项任务", "todos")
                     if todo.items() else "")
                  + "[/dim]")


def main():
    i18n.set_lang(config.LANGUAGE)
    ap = argparse.ArgumentParser(
        prog="wow", description="wow-agent terminal coding assistant")
    ap.add_argument("task", nargs="*", help=tr(
        "一次性任务，不给则进入交互模式",
        "one-shot task; omit to enter interactive mode"))
    ap.add_argument("--yolo", action="store_true", help=tr(
        "跳过命令执行确认", "skip command confirmations"))
    ap.add_argument("-V", "--version", action="store_true")
    args = ap.parse_args()
    if args.version:
        print(f"wow-agent v{__version__}")
        return

    if not config.API_KEY:
        console.print(tr("[yellow]首次使用，先配置服务商和 API key：[/yellow]",
                         "[yellow]First run: configure a provider and API "
                         "key:[/yellow]"))
        cmd_model()
        if not config.API_KEY:
            console.print(tr(
                "[red]仍未配置 key。可稍后在会话里用 /model 配置，"
                "或 export WOW_API_KEY=... 后重试[/red]",
                "[red]Still no key. Configure later with /model, or "
                "export WOW_API_KEY=... and retry[/red]"))
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
    _panel_line(tr("进入自主模式？", "Enter auto mode?"),
                f"bold #e8e8e8 on {PANEL_BG}")
    _panel_line(tr("y = 免逐步确认 · 上传/高危命令仍需批准 · 实时存档"
                   " · 回车 = 每步确认",
                   "y = no per-step confirm · uploads/dangerous still ask · "
                   "live autosave · enter = confirm each step"),
                f"#9a9ab0 on {PANEL_BG}")
    if not auto:
        try:
            ans = console.input("y/N > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            ans = ""
        auto = ans in ("y", "yes")
    state["auto"] = auto
    if auto:
        ui.session_allow = True
        _panel_line(tr("自主模式已开启", "Auto mode on"),
                    f"#9a9ab0 on {PANEL_BG}")

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
            msg = tr("对话已清空，新会话", "Conversation cleared, new session")
            console.print(f"[dim]{msg} {state['sid']}[/dim]")
            continue
        if line == "/help":
            console.print(help_text())
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
                console.print(f"[red]{tr('用法', 'Usage')}:[/red] "
                              "/mem save|use|rm|list|new")
                continue
            cmd_mem(line, messages, state, ui)
            continue
        if line.startswith("/language"):
            arg = line[len("/language"):].strip().lower()
            if arg in ("en", "zh"):
                i18n.set_lang(arg)
                config.save_env({"WOW_LANGUAGE": arg})
                COMMANDS.clear()
                COMMANDS.update(command_descriptions())
                console.print(
                    f"[green]✓[/green] "
                    + tr("语言已切换：中文（模型将用中文回复）",
                         "Language switched: English (model replies in "
                         "English)"))
            elif not arg:
                # 交互式菜单
                console.print(tr("选择语言:", "Select language:"))
                console.print("  1. " + tr("中文", "Chinese"))
                console.print("  2. " + tr("English", "English"))
                try:
                    choice = console.input(
                        tr("选择 [1/2/回车取消]: ", "Select [1/2/enter to cancel]: ")
                    ).strip()
                except (KeyboardInterrupt, EOFError):
                    console.print()
                    continue
                if choice == "1":
                    i18n.set_lang("zh")
                    config.save_env({"WOW_LANGUAGE": "zh"})
                    COMMANDS.clear()
                    COMMANDS.update(command_descriptions())
                    console.print(f"[green]✓[/green] {tr('语言已切换', 'Language switched')}")
                elif choice == "2":
                    i18n.set_lang("en")
                    config.save_env({"WOW_LANGUAGE": "en"})
                    COMMANDS.clear()
                    COMMANDS.update(command_descriptions())
                    console.print(f"[green]✓[/green] {tr('语言已切换', 'Language switched')}")
                else:
                    cur = tr("中文", "English") if i18n.LANG == "zh" \
                        else tr("中文", "English")
                    console.print(
                        tr(f"当前语言: {cur} · 用法: /language en|zh",
                           f"Current language: {cur} · usage: /language en|zh"))
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
        if line.startswith("/review"):
            scope = line[len("/review"):].strip() or "."
            console.print(f"\n[magenta]▪ "
                          + tr("只读代码审查", "Read-only code review")
                          + f"[/magenta] [dim]{scope}[/dim]")
            report = subagent.run(
                tr(f"审查目标: {scope}\n请开始只读调研并输出审查报告。",
                   f"Review target: {scope}\nStart the read-only research "
                   "and output the review report."),
                ui, tr("代码审查", "code review"), system=review_system())
            from rich.markdown import Markdown
            console.print(Markdown(report))
            continue
        if line.startswith("!"):
            out = _run_bash(line[1:], timeout=120)
            console.print(f"[dim]{out.strip()}[/dim]")
            continue
        if line.startswith("/"):
            console.print(f"[red]{tr('未知命令', 'Unknown command')}[/red] "
                          f"{line.split()[0]}，"
                          + tr("输入 / 可查看补全提示",
                               "type / to see completions"))
            continue
        run_task(ui, messages, line, state)

    console.print("[dim]" + tr("再见", "Bye") + "[/dim]")


if __name__ == "__main__":
    main()
