# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

import difflib
import json
import platform
import time
from datetime import date
from pathlib import Path

import httpx
import openai
from openai import OpenAI

from . import config, i18n, todo, undo
from .i18n import tr
from .subagent import run as run_subtask
from .tools import TOOLS_SCHEMA, is_dangerous, is_upload_like

FILE_TOOLS = ("write_file", "edit_file")

# 免费档（如 ox alpha）上游间歇抽风：连接失败/超时/限流/5xx 都值得重试；
# 401/403 属于 key 配错，重试无意义，直接报给用户。
TRANSIENT_ERRORS = (openai.APIConnectionError, openai.RateLimitError,
                    openai.InternalServerError)


def make_client():
    """统一客户端：关掉 SDK 内部重试（退避由 run_turn 控制），缩短超时快速失败，
    避免免费档上游卡死时一次调用就挂几分钟。"""
    return OpenAI(
        api_key=config.API_KEY or "none",
        base_url=config.BASE_URL,
        timeout=httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=10.0),
        max_retries=0,
    )


def full_schema():
    """内置工具 + MCP 桥接工具（未配置 MCP 时与静态表等价）。"""
    try:
        from . import mcp
        extra = mcp.schemas()
    except Exception:
        extra = []
    return list(TOOLS_SCHEMA) + extra


class EmptyReplyError(RuntimeError):
    """模型返回空内容且无工具调用（常见于免费模型不支持 tools）。"""


def system_prompt(cwd):
    # 开发者与证书信息
    dev_info = (
        "wow-agent 是由 GitHub 用户 uuzjw 独立开发的终端编码 Agent。\n"
        "项目地址: https://github.com/uuzjw/wow-agent\n"
        "许可证: MIT License\n\n"
        "MIT License 完整文本:\n"
        "Copyright (c) 2026 uuzjw\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        "of this software and associated documentation files (the \"Software\"), to deal\n"
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n\n"
    )
    
    if i18n.LANG == "zh":
        return (
            f"wow-agent 是由 GitHub 用户 uuzjw 独立开发的终端编码 Agent。\n"
            f"项目地址: https://github.com/uuzjw/wow-agent\n"
            f"许可证: MIT License\n\n"
            f"你是 wow-agent，一个运行在终端里的编码助手，底层模型是 {config.MODEL}。\n"
            f"工作目录: {cwd}\n"
            f"平台: {platform.system()} {platform.machine()}\n"
            f"日期: {date.today().isoformat()}\n\n"
            "规则:\n"
            "- 用简体中文回复\n"
            "- 回答简洁直接，不啰嗦\n"
            "- 修改文件前先 read_file 看现有内容；编辑优先用 edit_file 做精确替换\n"
            "- 探索代码用 glob_files / grep_search，目录列表可用 run_bash ls\n"
            "- 完成用户请求即停止，不做多余动作\n"
            "- 每次只做用户要求的事，未经允许不 commit、不删除文件\n"
            "- 联网查资料、下载、装包都可以；但严禁未经用户批准把本地文件、代码、\n"
            "密钥等数据上传到网络（git push、scp、curl POST 等都会被拦截确认）\n"
            "- 工具调用失败时：先分析报错根因（路径不对？依赖缺失？权限不足？），\n"
            "修复后再试；同一做法连败两次就换别的方案，禁止原样硬试\n"
            "- 声称完成之前必须验证：write/edit 之后回读改动处确认生效，\n"
            "代码改动要跑测试或 import 冒烟检查；验证不过就继续修，\n"
            "绝不凭空宣称已完成\n\n"
            "协作机制:\n"
            "- 收到多步骤任务，先 todo_write 拆解成带 priority 的计划（大任务用 parent "
            "拆子任务），随后每完成一步立即 todo_write 更新状态和 note；单步小任务不必用\n"
            "- 需要大范围查代码、调研方案时，用 task 派只读子代理去搜，\n"
            "只让它回结论，避免主对话被文件内容塞满")
    return (
        "wow-agent is developed by GitHub user uuzjw. "
        "Project: https://github.com/uuzjw/wow-agent\n"
        "License: MIT License\n\n"
        f"You are wow-agent, a coding assistant running in a terminal, "
        f"powered by {config.MODEL}.\n"
        f"Working directory: {cwd}\n"
        f"Platform: {platform.system()} {platform.machine()}\n"
        f"Date: {date.today().isoformat()}\n\n"
        "Rules:\n"
        "- Reply in English\n"
        "- Be concise and direct, no fluff\n"
        "- read_file before modifying; prefer edit_file for precise edits\n"
        "- Use glob_files / grep_search to explore code; run_bash ls for listings\n"
        "- Stop once the request is fulfilled; no extra actions\n"
        "- Only do what the user asked; never commit or delete files without permission\n"
        "- Web lookups, downloads and installs are fine; NEVER upload local "
        "files, code or secrets without approval (git push, scp, curl POST "
        "are intercepted for confirmation)\n"
        "- When a tool call fails: analyze the root cause first (wrong path? "
        "missing dependency? permissions?), fix and retry; after two failures "
        "with the same approach switch strategies — never retry blindly\n"
        "- Verify before claiming done: after write/edit re-read the change; "
        "for code run tests or an import smoke check; if verification fails "
        "keep fixing — never claim success out of thin air\n\n"
        "Collaboration:\n"
        "- For multi-step tasks first todo_write a plan with priorities "
        "(use parent for subtasks), then update status/note via todo_write "
        "after each step; single-step tasks don't need it\n"
        "- For broad code research use task to dispatch a read-only "
        "subagent and bring back only conclusions, keeping the main "
        "context clean")


def est_tokens(messages):
    """粗略估算上下文 token 数：中文≈1 token/字，英文≈0.3 token/字符。"""
    total = 0
    for m in messages:
        total += 4
        c = m.get("content")
        if isinstance(c, str):
            for ch in c:
                total += 1.0 if ord(ch) > 127 else 0.3
        for tc in m.get("tool_calls") or []:
            total += len(tc["function"]["arguments"]) * 0.3
    return int(total)


def _diff_lines(before, after, path):
    d = list(difflib.unified_diff(
        (before or "").splitlines(), (after or "").splitlines(),
        fromfile=path, tofile=path, lineterm="", n=1))
    if d and d[0].startswith("---"):
        d = d[2:]
    return d


def _read_maybe(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _stream_assistant(client, messages, ui, tools_schema=None, label=None):
    ui.think_begin(label or tr(f"思考中 · {config.MODEL}",
                               f"thinking · {config.MODEL}"))
    stream = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        tools=tools_schema if tools_schema is not None else full_schema(),
        stream=True,
    )
    content_parts = []
    tool_calls = {}
    got = False
    finish = None
    think_n = 0
    try:
        for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta
            if delta is None:
                continue
            if not got:
                ui.think_end()
                got = True
            rc = (getattr(delta, "reasoning_content", None)
                  or getattr(delta, "reasoning", None))
            if rc:
                think_n += len(rc)
                ui.think_update(tr(
                    f"思考中 · {config.MODEL}（已思考 {think_n} 字）",
                    f"thinking · {config.MODEL} ({think_n} chars so far)"))
            if delta.content:
                content_parts.append(delta.content)
                ui.text_delta(delta.content)
            for tc in delta.tool_calls or []:
                slot = tool_calls.setdefault(
                    tc.index,
                    {"id": "", "type": "function",
                     "function": {"name": "", "arguments": ""}},
                )
                if tc.id:
                    slot["id"] += tc.id
                if tc.function and tc.function.name:
                    slot["function"]["name"] += tc.function.name
                if tc.function and tc.function.arguments:
                    slot["function"]["arguments"] += tc.function.arguments
            if choice.finish_reason:
                finish = choice.finish_reason
    finally:
        ui.think_end()
    if not tool_calls and not any(p.strip() for p in content_parts):
        raise EmptyReplyError(tr(
            f"模型返回空回复（finish_reason={finish}），"
            "该模型可能不支持工具调用；可 /model 切换到 "
            "nemotron-3-ultra-free 或 hy3-free",
            f"Empty reply (finish_reason={finish}); the model may not "
            "support tool calls — /model to switch to nemotron-3-ultra-free "
            "or hy3-free"))
    msg = {"role": "assistant", "content": "".join(content_parts)}
    if tool_calls:
        msg["tool_calls"] = [tool_calls[i] for i in sorted(tool_calls)]
    messages.append(msg)
    return msg


def _execute_tool(call, ui, cid=""):
    name = call["function"]["name"]
    raw = call["function"]["arguments"]
    try:
        args = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return f"[错误] 工具参数不是合法 JSON: {raw}", 0.0

    if name == "run_bash":
        cmd = str(args.get("command", ""))
        if is_dangerous(cmd):
            if not ui.confirm(f"[red]高危[/red] {cmd}", force=True):
                return "[用户拒绝执行高危命令]", 0.0
        elif config.UPLOAD_GUARD and is_upload_like(cmd):
            if not ui.confirm(f"[red]外传风险·需批准[/red] {cmd}",
                              force=True):
                return "[用户拒绝执行外传命令]", 0.0
        elif not ui.confirm(cmd):
            return "[用户拒绝执行该命令]", 0.0

    before = existed = None
    p = None
    if name in FILE_TOOLS and isinstance(args.get("path"), str):
        p = Path(args["path"]).expanduser()
        existed = p.exists()
        before = _read_maybe(p) if existed else None

    t0 = time.perf_counter()
    try:
        if name == "task":
            result = run_subtask(str(args.get("prompt") or ""), ui,
                                 str(args.get("description") or ""))
        elif name.startswith("mcp__"):
            from . import mcp
            result = mcp.execute(name, args)
        else:
            from .tools import execute
            result = execute(name, args)
    except Exception as e:
        result = f"[工具执行出错] {e}: {type(e).__name__}"

    if name == "todo_write":
        ui.set_todos(todo.items())
    elapsed = time.perf_counter() - t0

    if (name in FILE_TOOLS
            and not result.lstrip().startswith(
                ("[错误]", "[工具执行出错]", "[用户拒绝]"))
            and todo.phase() == "executing"):
        todo.set_phase("verifying")

    if p is not None:
        after = _read_maybe(p) if p.exists() else None
        if result.lstrip().startswith(("[错误]", "[工具执行出错]")):
            pass
        elif after != before:
            undo.push(str(p), bool(existed), before, cid=cid)
            ui.diff(_diff_lines(before, after, str(p)),
                    is_new=(before is None))
    return result, elapsed


def _call_sig(call):
    """规范化工具调用签名（参数键排序），用于识别原地打转的重复调用。"""
    raw = call["function"].get("arguments") or "{}"
    try:
        args = json.dumps(json.loads(raw), sort_keys=True, ensure_ascii=False)
    except json.JSONDecodeError:
        args = raw
    return (call["function"]["name"], args)


def run_turn(client, messages, ui, on_progress=None):
    turns = 0
    t0 = time.perf_counter()
    cid = f"t{time.time_ns()}"
    last_sig = None
    repeat_n = 0
    auth_n = 0
    for _ in range(config.MAX_ITER):
        turns += 1
        if getattr(ui, "abort_requested", False):
            raise KeyboardInterrupt
        msg = None
        for attempt in range(6):
            ui.text_begin()
            ok = False
            try:
                msg = _stream_assistant(client, messages, ui)
                ok = True
                break
            except (EmptyReplyError,) + TRANSIENT_ERRORS as e:
                wait = min(2 ** attempt, 8)
                if attempt < 5:
                    if isinstance(e, EmptyReplyError):
                        reason, kind = str(e), tr("空回复", "empty reply")
                    else:
                        reason = f"{type(e).__name__}: {str(e)[:100]}"
                        kind = tr("上游错误", "upstream error")
                    ui.console.print(
                        f"[yellow]{reason}[/yellow]\n"
                        f"[yellow]· {kind}，"
                        + tr(f"{wait}s 后自动重试 {attempt + 1}/5…"
                             "（半截输出已丢弃）",
                             f"retrying in {wait}s ({attempt + 1}/5…"
                             ", partial output discarded)")
                        + "[/yellow]")
                    time.sleep(wait)
                else:
                    if isinstance(e, EmptyReplyError):
                        ui.console.print(f"[red]{e}[/red]")
                    else:
                        ui.console.print(
                            f"[red]"
                            + tr("上游连续 6 次失败，放弃本轮: ",
                                 "Upstream failed 6 times, giving up: ")
                            + f"{type(e).__name__}: {str(e)[:160]}[/red]")
                    return False, {"turns": turns,
                                   "elapsed": time.perf_counter() - t0,
                                   "empty": True, "cid": cid}
            except openai.AuthenticationError:
                # 实测 Zen 免费档网关过载时会间歇性乱报 401（key 实际有效），
                # 先重试两次再判死，避免误杀真 key
                auth_n += 1
                if auth_n <= 2:
                    ui.console.print(
                        f"[yellow]· "
                        + tr("401（上游偶发，key 可能有效），",
                             "401 (upstream hiccup, key may be valid), ")
                        + tr(f"重试 {auth_n}/2…", f"retry {auth_n}/2…")
                        + "[/yellow]")
                    time.sleep(1)
                    continue
                raise
            finally:
                if ok:
                    ui.text_end()
                else:
                    ui.text_discard()
        if callable(on_progress):
            on_progress()
        calls = msg.get("tool_calls")
        if not calls:
            return True, {"turns": turns,
                          "elapsed": time.perf_counter() - t0,
                          "cid": cid}
        for call in calls:
            if getattr(ui, "abort_requested", False):
                raise KeyboardInterrupt
            name = call["function"]["name"]
            ui.tool_start(name, call["function"]["arguments"])
            result, dt = _execute_tool(call, ui, cid=cid)
            ui.tool_result(name, result, dt)
            content = result[:20000]
            sig = _call_sig(call)
            repeat_n = repeat_n + 1 if sig == last_sig else 0
            last_sig = sig
            if repeat_n >= 2:
                content += tr(
                    "\n[系统警告] 同一工具调用已连续 3 次得到相同结果，"
                    "禁止再原样重试：先分析失败或无进展的根因，换一种做法，"
                    "或直接向用户说明障碍请求决策。",
                    "\n[SYSTEM WARNING] The same tool call returned the "
                    "same result 3 times in a row. Do NOT retry it as-is: "
                    "analyze the root cause, try a different approach, or "
                    "explain the blocker to the user and ask for a "
                    "decision.")
                repeat_n = 0
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": content,
            })
            if callable(on_progress):
                on_progress()
    return False, {"turns": turns, "elapsed": time.perf_counter() - t0,
                   "cid": cid}


COMPACT_PROMPT_ZH = (
    "请把以下 agent 对话历史压缩为一份摘要，必须保留：\n"
    "1. 用户的核心需求和偏好\n"
    "2. 已完成的关键操作及涉及的文件路径\n"
    "3. 重要结论和决定\n"
    "4. 未完成的事项\n"
    "直接输出摘要正文，不要客套话。")

COMPACT_PROMPT_EN = (
    "Compress the following agent conversation history into a summary. "
    "Keep:\n"
    "1. The user's core needs and preferences\n"
    "2. Key completed operations and file paths involved\n"
    "3. Important conclusions and decisions\n"
    "4. Unfinished items\n"
    "Output only the summary text, no pleasantries.")


def compact(client, messages, ui=None, extra=None):
    """把除 system 外的历史压缩成一条摘要消息，返回新消息列表。"""
    convo = [m for m in messages if m.get("role") != "system"]
    if not convo:
        return messages
    parts = []
    for m in convo:
        role = m.get("role")
        c = m.get("content") or ""
        for tc in m.get("tool_calls") or []:
            c += (c and "\n" or "") + (
                f"[调用 {tc['function']['name']} "
                f"{tc['function']['arguments'][:200]}]")
        parts.append(f"[{role}] {c}" if c.strip() else "")
    payload = "\n".join(p for p in parts if p)
    prompt = tr(COMPACT_PROMPT_ZH, COMPACT_PROMPT_EN) \
        + (tr(f"\n额外要求: {extra}", f"\nExtra requirements: {extra}")
           if extra else "")
    stream = client.chat.completions.create(
        model=config.MODEL,
        messages=[{"role": "user",
                   "content": f"{prompt}\n\n{payload}"}],
        stream=True,
    )
    out = []
    if ui is not None:
        ui.text_begin()
    try:
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta is not None and delta.content:
                out.append(delta.content)
                if ui is not None:
                    ui.text_delta(delta.content)
    finally:
        if ui is not None:
            ui.text_end()
    summary = "".join(out).strip()
    sysmsg = next((m for m in messages if m.get("role") == "system"),
                  {"role": "system",
                   "content": system_prompt(str(Path.cwd()))})
    new = [sysmsg, {
        "role": "user",
        "content": f"[对话历史摘要]\n{summary}\n\n"
                   "（以上是之前对话的压缩存档，请基于它继续任务）",
    }]
    return new
