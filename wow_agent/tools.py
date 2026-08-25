# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

import fnmatch
import os
import re
import shutil
import subprocess
from pathlib import Path

from . import i18n, todo
from .i18n import tr

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
            "name": "code_index",
            "description": (
                "查询项目索引（文件树 + Python 类/函数/import 符号表）。"
                "找代码先查这里再精读，比反复 find/grep 省得多。"
                "action=summary 项目概览 | search 按符号名模糊搜 | "
                "file 看单文件结构 | rebuild 强制重建"),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string",
                               "enum": ["summary", "search", "file", "rebuild"],
                               "description": "默认 summary"},
                    "query": {"type": "string",
                              "description": "search 时的关键词"},
                    "path": {"type": "string",
                             "description": "file 时相对项目根的路径"},
                },
                "required": [],
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
                    "phase": {
                        "type": "string",
                        "enum": ["planning", "executing", "verifying",
                                 "done", "failed"],
                        "description": ("整体任务阶段状态机：planning 规划 → executing 动手 "
                                        "→ verifying 验证改动 → done 完成 / failed 受阻"
                                        "（需要用户决策）。随进展同步更新"),
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
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "显示 Git 工作区状态（修改、暂存、未跟踪文件）。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "显示工作区或暂存区的 diff。可指定文件路径。",
            "parameters": {
                "type": "object",
                "properties": {
                    "staged": {"type": "boolean", "description": "显示暂存区 diff（默认 false，显示工作区）"},
                    "path": {"type": "string", "description": "可选，限定文件路径"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_log",
            "description": "显示提交历史。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "显示条数，默认 10"},
                    "oneline": {"type": "boolean", "description": "单行模式，默认 true"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_add",
            "description": "将文件加入暂存区。",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {"type": "array", "items": {"type": "string"}, "description": "文件路径列表，默认 ['.'] 全部"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "提交暂存区更改。可选自动生成提交信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "提交信息，留空则自动生成"},
                    "amend": {"type": "boolean", "description": "修正上一次提交，默认 false"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_push",
            "description": "推送到远程仓库。",
            "parameters": {
                "type": "object",
                "properties": {
                    "remote": {"type": "string", "description": "远程名，默认 origin"},
                    "branch": {"type": "string", "description": "分支名，默认当前分支"},
                    "force": {"type": "boolean", "description": "强制推送，默认 false"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_branch",
            "description": "列出、创建、删除分支。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "create", "delete", "switch"], "description": "操作类型"},
                    "name": {"type": "string", "description": "分支名（create/switch/delete 时必填）"},
                    "start_point": {"type": "string", "description": "创建时的起点，默认 HEAD"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff_cached",
            "description": "显示暂存区 diff（等同于 git_diff staged=true）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "可选，限定文件路径"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_log_graph",
            "description": "显示图形化提交历史（类似 git log --graph --oneline）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "显示条数，默认 20"},
                },
                "required": [],
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
        return tr(f"[错误] 命令超过 {timeout}s 未完成，已终止",
                  f"[error] Command exceeded {timeout}s timeout, terminated")


def _read_file(path, offset=1, limit=0):
    """分块读取：头部带总行数/当前区间/续读 offset，大文件不再一次吞爆上下文。"""
    p = Path(path).expanduser()
    if not p.exists():
        return tr(f"[错误] 文件不存在: {p}", f"[error] File not found: {p}")
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)
    start = min(max(int(offset), 1), max(total, 1)) - 1
    n = int(limit) if int(limit) > 0 else 2000
    chunk = lines[start:start + n]
    if not total:
        head = tr(f"[{p.name} 空文件]", f"[{p.name} empty]")
    else:
        head = (tr(f"[{p.name} 共 {total} 行 · ",
                     f"[{p.name} total {total} lines · ")
                + tr(f"显示第 {start + 1}-{start + len(chunk)} 行]",
                     f"showing lines {start + 1}-{start + len(chunk)}]"))
        if start + len(chunk) < total:
            head += tr(f" · 续读 offset={start + len(chunk) + 1}",
                       f" · next offset={start + len(chunk) + 1}")
    return _truncate(f"{head}\n" + "\n".join(chunk))


def _write_file(path, content):
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return tr(f"已写入 {p}（{len(content)} 字符）",
              f"Written {p} ({len(content)} chars)")


def _edit_file(path, old_string, new_string):
    p = Path(path).expanduser()
    if not p.exists():
        return tr(f"[错误] 文件不存在: {p}", f"[error] File not found: {p}")
    text = p.read_text(encoding="utf-8")
    n = text.count(old_string)
    if n == 0:
        return tr("[错误] old_string 未找到",
                  "[error] old_string not found")
    if n > 1:
        return tr(f"[错误] old_string 出现了 {n} 次，需提供更长的上下文使其唯一",
                  f"[error] old_string appears {n} times; provide longer "
                  "context to make it unique")
    p.write_text(text.replace(old_string, new_string, 1), encoding="utf-8")
    return tr(f"已修改 {p}", f"Edited {p}")


def _glob_files(pattern, path="."):
    root = Path(path).expanduser()
    matches = sorted(
        str(m) for m in root.glob(pattern)
        if m.is_file() and ".git" not in m.parts
    )
    return _truncate("\n".join(matches) if matches else
                     tr("[无匹配]", "[no matches]"))


def _grep_search(pattern, path=".", include=None):
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return tr(f"[错误] 正则不合法: {e}",
                  f"[error] Invalid regex: {e}")
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
                        hits.append(tr("...[匹配过多，已截断]",
                                       "...[truncated, too many matches]"))
                        return _truncate("\n".join(hits))
        except OSError:
            continue
    return _truncate("\n".join(hits) if hits else
                     tr("[无匹配]", "[no matches]"))


def _code_index(args):
    from . import indexer
    return indexer.query(action=str(args.get("action") or "summary"),
                         q=str(args.get("query") or ""),
                         path=str(args.get("path") or ""))


# ===== Git 工具实现 =====

def _git(cmd_args, cwd=None):
    """执行 git 命令，返回 (stdout, stderr, returncode)"""
    if cwd is None:
        cwd = Path.cwd()
    cmd = ["git"] + cmd_args
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=30)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 124
    except Exception as e:
        return "", str(e), 1


def _git_status():
    out, err, rc = _git(["status", "--short", "--branch"])
    if rc != 0:
        return tr(f"[错误] git status 失败: {err}", f"[error] git status failed: {err}")
    if not out:
        return tr("工作区干净", "Working tree clean")
    return f"[branch] {out.splitlines()[0]}\n{out}"


def _git_diff(staged=False, path=None):
    args = ["diff"]
    if staged:
        args.append("--cached")
    if path:
        args.extend(["--", path])
    out, err, rc = _git(args)
    if rc != 0:
        return tr(f"[错误] git diff 失败: {err}", f"[error] git diff failed: {err}")
    if not out:
        return tr("无差异", "No changes")
    return _truncate(out)


def _git_log(limit=10, oneline=True):
    args = ["log"]
    if oneline:
        args.append("--oneline")
    args.extend(["-n", str(limit)])
    out, err, rc = _git(args)
    if rc != 0:
        return tr(f"[错误] git log 失败: {err}", f"[error] git log failed: {err}")
    if not out:
        return tr("无提交记录", "No commits")
    return out


def _git_add(paths):
    args = ["add"] + paths
    out, err, rc = _git(["add"] + paths)
    if rc != 0:
        return tr(f"[错误] git add 失败: {err}", f"[error] git add failed: {err}")
    return tr(f"已添加: {', '.join(paths)}", f"Added: {', '.join(paths)}")


def _git_commit(message=None, amend=False):
    if amend:
        args = ["commit", "--amend", "--no-edit"]
    elif message:
        args = ["commit", "-m", message]
    else:
        # 自动生成提交信息
        out, _, _ = _git(["diff", "--cached", "--stat"])
        if not out:
            return tr("暂存区为空，无需提交", "Nothing to commit")
        args = ["commit", "-m", f"auto: {out.splitlines()[0][:50]}"]
    out, err, rc = _git(args)
    if rc != 0:
        return tr(f"[错误] git commit 失败: {err}", f"[error] git commit failed: {err}")
    return tr(f"已提交: {out.strip()}", f"Committed: {out.strip()}")


def _git_push(remote="origin", branch=None, force=False):
    args = ["push", remote]
    if force:
        args.append("--force")
    if branch:
        args.append(branch)
    out, err, rc = _git(args)
    if rc != 0:
        return tr(f"[错误] git push 失败: {err}", f"[error] git push failed: {err}")
    return tr(f"已推送到 {remote}", f"Pushed to {remote}")


def _git_branch(action, name=None, start_point=None):
    if action == "list":
        out, err, rc = _git(["branch", "-a"])
        if rc != 0:
            return tr(f"[错误] git branch 失败: {err}", f"[error] git branch failed: {err}")
        return out or tr("无分支", "No branches")
    elif action == "create":
        if not name:
            return tr("[错误] 创建分支需指定 name", "[error] create branch requires name")
        args = ["branch", name]
        if start_point:
            args.append(start_point)
        out, err, rc = _git(args)
        if rc != 0:
            return tr(f"[错误] 创建分支失败: {err}", f"[error] create branch failed: {err}")
        return tr(f"已创建分支 {name}", f"Created branch {name}")
    elif action == "delete":
        if not name:
            return tr("[错误] 删除分支需指定 name", "[error] delete branch requires name")
        out, err, rc = _git(["branch", "-d", name])
        if rc != 0:
            out, err, rc = _git(["branch", "-D", name])
            if rc != 0:
                return tr(f"[错误] 删除分支失败: {err}", f"[error] delete branch failed: {err}")
        return tr(f"已删除分支 {name}", f"Deleted branch {name}")
    elif action == "switch":
        if not name:
            return tr("[错误] 切换分支需指定 name", "[error] switch branch requires name")
        out, err, rc = _git(["switch", name])
        if rc != 0:
            return tr(f"[错误] 切换分支失败: {err}", f"[error] switch branch failed: {err}")
        return tr(f"已切换到分支 {name}", f"Switched to branch {name}")
    else:
        return tr(f"[错误] 未知 action: {action}", f"[error] unknown action: {action}")


def _git_log_graph(limit=20):
    args = ["log", "--graph", "--oneline", "--all", f"-n{limit}"]
    out, err, rc = _git(args)
    if rc != 0:
        return tr(f"[错误] git log 失败: {err}", f"[error] git log failed: {err}")
    if not out:
        return tr("无提交记录", "No commits")
    return out


EXECUTORS = {
    "run_bash": lambda a: _run_bash(a["command"], int(a.get("timeout", 60))),
    "read_file": lambda a: _read_file(a["path"], int(a.get("offset", 1)),
                                      int(a.get("limit", 0))),
    "write_file": lambda a: _write_file(a["path"], a["content"]),
    "edit_file": lambda a: _edit_file(a["path"], a["old_string"], a["new_string"]),
    "glob_files": lambda a: _glob_files(a["pattern"], a.get("path", ".")),
    "grep_search": lambda a: _grep_search(a["pattern"], a.get("path", "."), a.get("include")),
    "code_index": _code_index,
    "todo_write": todo.apply,
    "git_status": lambda a: _git_status(),
    "git_diff": lambda a: _git_diff(a.get("staged", False), a.get("path")),
    "git_log": lambda a: _git_log(int(a.get("limit", 10)), a.get("oneline", True)),
    "git_add": lambda a: _git_add(a.get("paths", ["."])),
    "git_commit": lambda a: _git_commit(a.get("message"), a.get("amend", False)),
    "git_push": lambda a: _git_push(a.get("remote", "origin"), a.get("branch"), a.get("force", False)),
    "git_branch": lambda a: _git_branch(a["action"], a.get("name"), a.get("start_point")),
    "git_diff_cached": lambda a: _git_diff(True, a.get("path")),
    "git_log_graph": lambda a: _git_log_graph(int(a.get("limit", 20))),
}


def execute(name, args):
    fn = EXECUTORS.get(name)
    if fn is None:
        return f"[错误] 未知工具: {name}"
    return fn(args)
