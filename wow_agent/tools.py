# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

import fnmatch
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import todo

MAX_OUTPUT = 10000

NET_BLOCK = os.environ.get("WOW_SAFE_MODE", "1").lower() not in (
    "0", "false", "no")

_unshare_usable = None


def _net_sandbox_prefix():
    """返回断网执行前缀：优先 unshare -n 网络命名空间，不可用则 None。"""
    global _unshare_usable
    if not shutil.which("unshare"):
        return None
    if _unshare_usable is None:
        try:
            r = subprocess.run(["unshare", "-n", "true"], capture_output=True,
                               timeout=10)
            _unshare_usable = r.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            _unshare_usable = False
    return ["unshare", "-n"] if _unshare_usable else None


_BLACKHOLE_ENV = {
    "HTTP_PROXY": "http://127.0.0.1:9",
    "HTTPS_PROXY": "http://127.0.0.1:9",
    "ALL_PROXY": "http://127.0.0.1:9",
    "http_proxy": "http://127.0.0.1:9",
    "https_proxy": "http://127.0.0.1:9",
    "all_proxy": "http://127.0.0.1:9",
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "在工作目录用 bash 执行 shell 命令并返回 stdout/stderr 和退出码。用于查看目录、运行程序、git、安装依赖等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                    "timeout": {"type": "integer", "description": "超时秒数，默认 60"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "读取文本文件内容，返回头部元信息（总行数/当前区间/续读 offset）。"
                "大文件先用默认调用看前 2000 行，再用 offset+limit 分块续读，"
                "不要试图一次吞下整个文件。"),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "offset": {"type": "integer",
                               "description": "起始行号（从 1 开始），默认 1"},
                    "limit": {"type": "integer",
                              "description": "本次读取的行数，默认 2000"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入文件（覆盖已有内容），自动创建父目录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "完整文件内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "把文件中 old_string 的唯一一次出现替换为 new_string，old_string 必须在文件中恰好出现一次。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob_files",
            "description": "按通配符模式查找文件，如 **/*.py。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "description": "搜索根目录，默认当前目录"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "用正则在文件内容中搜索，返回匹配行及行号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "正则表达式"},
                    "path": {"type": "string", "description": "文件或目录，默认当前目录"},
                    "include": {"type": "string", "description": "文件名过滤如 *.py"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "todo_write",
            "description": (
                "维护当前任务的计划清单（每次全量提交整个清单）。"
                "收到多步骤任务必须先用它拆解：按优先级标 priority，大任务可拆 parent 子任务；"
                "开工时把一条置 in_progress，完成立即置 completed 并在 note 写关键进展。"),
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "description": "完整清单（包含所有条目，未变的也要带上）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "唯一 id，如 1/2/3.1"},
                                "content": {"type": "string", "description": "任务内容"},
                                "status": {"type": "string",
                                           "enum": ["pending", "in_progress", "completed"]},
                                "priority": {"type": "string",
                                             "enum": ["high", "medium", "low"]},
                                "parent": {"type": "string", "description": "父任务 id，顶级留空"},
                                "note": {"type": "string", "description": "思路/进展备注"},
                            },
                            "required": ["content"],
                        },
                    },
                },
                "required": ["todos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task",
            "description": (
                "派出只读调研子代理：它在全新干净上下文里查代码、验证方案，"
                "只把结论文本带回主对话。需要大量搜索阅读时用它，避免污染主上下文。"
                "prompt 要写清调研目标、范围和期望的产出格式。"),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "一句话描述（3-5 个词）"},
                    "prompt": {"type": "string", "description": "详细的调研指令"},
                },
                "required": ["description", "prompt"],
            },
        },
    },
]


def _truncate(s):
    return s if len(s) <= MAX_OUTPUT else s[:MAX_OUTPUT] + "\n...[输出已截断]"


_UPLOAD_RX = [
    re.compile(p)
    for p in (
        r"\bcurl?\b[^|;&]*\s(-d|--data|-F|--form|-T|--upload-file|--json"
        r"|-X[ =](POST|PUT|PATCH)|--request[ =](POST|PUT|PATCH))",
        r"\bwget\b[^|;&]*--post-(data|file)",
        r"\b(scp|sftp)\b",
        r"\bftp\b[^|;&]*\b(put|mput|send)\b",
        r"\brsync\b[^|;&]*[\w.@-]+:",
        r"\bgit\s+push\b",
        r"\bssh\b",
        r"\b(twine|poetry|npm|pnpm|yarn|huggingface-cli)"
        r"[^|;&]*(upload|publish)",
        r"\bgh\s+(release|repo)\b[^|;&]*(create|upload)",
        r"\baws\b[^|;&]*s3://",
        r"\bgcloud\b[^|;&]*\b(cp|mv|rsync|compose)\b",
        r"\b(nc|ncat|netcat)\b[^|;&]*[<>]",
        r">\s*/dev/(tcp|udp)/",
    )
]


def is_upload_like(command):
    """识别疑似向外部上传/外发数据的命令；下载、查看类不受影响。"""
    c = " ".join(str(command).split())
    return any(rx.search(c) for rx in _UPLOAD_RX)


_DANGER_PATTERNS = [
    re.compile(r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\b[^|;&]*\s/+(?:\s|$)"),
    re.compile(r"\bmkfs(\.\w+)?\b"),
    re.compile(r"\bdd\b[^|;&]*of=/dev/(?:sd|nvme|hd|vd|mmcblk)"),
    re.compile(r":\s*\(\)\s*\{.*\}\s*;\s*:"),
    re.compile(r"\b(shutdown|reboot|poweroff|halt)\b"),
    re.compile(r"\bchmod\s+-R\s+777\s+/(?:\s|$)"),
    re.compile(r">\s*/dev/sd[a-z]"),
    re.compile(r"\bgit\s+push\s+.*--force\b"),
]


def is_dangerous(command):
    """高危命令识别：无论什么模式都必须人工二次确认。"""
    c = " ".join(str(command).split())
    return any(rx.search(c) for rx in _DANGER_PATTERNS)


def _run_bash(command, timeout=60):
    env = None
    cmd = command
    if NET_BLOCK:
        prefix = _net_sandbox_prefix()
        if prefix:
            cmd = " ".join(prefix) + " " + command
        else:
            env = dict(os.environ)
            env.update(_BLACKHOLE_ENV)
    try:
        r = subprocess.run(
            cmd, shell=True, executable="/bin/bash", capture_output=True,
            text=True, timeout=timeout, cwd=str(Path.cwd()), env=env,
        )
        out = ""
        if r.stdout:
            out += r.stdout
        if r.stderr:
            out += "\n[stderr]\n" + r.stderr
        return _truncate(f"[exit {r.returncode}]\n{out.strip()}")
    except subprocess.TimeoutExpired:
        return f"[错误] 命令超过 {timeout}s 未完成，已终止"


def _read_file(path, offset=1, limit=0):
    """分块读取：头部带总行数/当前区间/续读 offset，大文件不再一次吞爆上下文。"""
    p = Path(path).expanduser()
    if not p.exists():
        return f"[错误] 文件不存在: {p}"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)
    start = min(max(int(offset), 1), max(total, 1)) - 1
    n = int(limit) if int(limit) > 0 else 2000
    chunk = lines[start:start + n]
    if not total:
        head = f"[{p.name} 空文件]"
    else:
        head = (f"[{p.name} 共 {total} 行 · "
                f"显示第 {start + 1}-{start + len(chunk)} 行]")
        if start + len(chunk) < total:
            head += f" · 续读 offset={start + len(chunk) + 1}"
    return _truncate(f"{head}\n" + "\n".join(chunk))


def _write_file(path, content):
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"已写入 {p}（{len(content)} 字符）"


def _edit_file(path, old_string, new_string):
    p = Path(path).expanduser()
    if not p.exists():
        return f"[错误] 文件不存在: {p}"
    text = p.read_text(encoding="utf-8")
    n = text.count(old_string)
    if n == 0:
        return "[错误] old_string 未找到"
    if n > 1:
        return f"[错误] old_string 出现了 {n} 次，需提供更长的上下文使其唯一"
    p.write_text(text.replace(old_string, new_string, 1), encoding="utf-8")
    return f"已修改 {p}"


def _glob_files(pattern, path="."):
    root = Path(path).expanduser()
    matches = sorted(
        str(m) for m in root.glob(pattern)
        if m.is_file() and ".git" not in m.parts
    )
    return _truncate("\n".join(matches) if matches else "[无匹配]")


def _grep_search(pattern, path=".", include=None):
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"[错误] 正则不合法: {e}"
    root = Path(path).expanduser()
    files = [root] if root.is_file() else (
        f for f in root.rglob("*")
        if f.is_file() and ".git" not in f.parts
        and (include is None or fnmatch.fnmatch(f.name, include))
    )
    hits = []
    for f in files:
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{f}:{i}: {line.strip()}")
                    if len(hits) >= 200:
                        hits.append("...[匹配过多，已截断]")
                        return _truncate("\n".join(hits))
        except OSError:
            continue
    return _truncate("\n".join(hits) if hits else "[无匹配]")


EXECUTORS = {
    "run_bash": lambda a: _run_bash(a["command"], int(a.get("timeout", 60))),
    "read_file": lambda a: _read_file(a["path"], int(a.get("offset", 1)),
                                      int(a.get("limit", 0))),
    "write_file": lambda a: _write_file(a["path"], a["content"]),
    "edit_file": lambda a: _edit_file(a["path"], a["old_string"], a["new_string"]),
    "glob_files": lambda a: _glob_files(a["pattern"], a.get("path", ".")),
    "grep_search": lambda a: _grep_search(a["pattern"], a.get("path", "."), a.get("include")),
    "todo_write": todo.apply,
}


def execute(name, args):
    fn = EXECUTORS.get(name)
    if fn is None:
        return f"[错误] 未知工具: {name}"
    return fn(args)
