# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""任务清单：todo_write 维护带状态/优先级/父子结构的计划树，实时持久化。"""

import json
import os
import time
from pathlib import Path

ROOT = Path(os.environ.get("WOW_AGENT_HOME", str(Path.home()))) / ".wow-agent"
STATE = ROOT / "todo.json"
STATUSES = ("pending", "in_progress", "completed")
PRIORITIES = {"high": 0, "medium": 1, "low": 2}

# 任务状态机：规划 → 执行 → 验证 → 完成/受阻，模型可显式切换，文件改动自动推进
PHASES = ("planning", "executing", "verifying", "done", "failed")
PHASE_LABEL = {
    "planning": "📋 规划中",
    "executing": "⚙ 执行中",
    "verifying": "🔍 验证中",
    "done": "✅ 已完成",
    "failed": "❌ 受阻",
}
_phase = "planning"


def phase():
    return _phase


def set_phase(p):
    global _phase
    if p in PHASES:
        _phase = p
        _persist()
        return True
    return False

_items = []


def items():
    return _items


def counts():
    total = len(_items)
    done = sum(1 for t in _items if t["status"] == "completed")
    prog = sum(1 for t in _items if t["status"] == "in_progress")
    return total, done, prog


def set_all(rows):
    global _items
    _items = _normalize(rows)
    _persist()


def reset():
    global _items, _phase
    _items = []
    _phase = "planning"
    _persist()


def apply(args):
    rows = args.get("todos") if isinstance(args, dict) else None
    if not isinstance(rows, list) or not rows:
        return "[错误] todos 必须是非空数组（每次全量提交整个清单）"
    set_all(rows)
    if isinstance(args.get("phase"), str):
        set_phase(args["phase"].strip().lower())
    total, done, prog = counts()
    cur = next((t for t in _items if t["status"] == "in_progress"), None)
    msg = f"清单已更新: 共{total}项 · 完成{done} · 阶段:{PHASE_LABEL[_phase]}"
    if prog:
        msg += f" · 进行中{prog}"
    if cur:
        msg += f" | 当前: [{cur['id']}] {cur['content']}"
    return msg


def sorted_tree():
    children = {}
    for t in _items:
        children.setdefault(t["parent"], []).append(t)
    out, seen = [], set()

    def walk(pid, depth):
        for t in sorted(children.get(pid, []),
                        key=lambda x: PRIORITIES.get(x["priority"], 1)):
            if t["id"] in seen:
                continue
            seen.add(t["id"])
            out.append((t, depth))
            walk(t["id"], depth + 1)

    walk("", 0)
    for t in _items:
        if t["id"] not in seen:
            out.append((t, 0))
    return out


def save(sid):
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        (ROOT / f"todo-{sid}.json").write_text(
            json.dumps(_items, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _normalize(rows):
    out, seen = [], set()
    for i, r in enumerate(rows, 1):
        if not isinstance(r, dict):
            continue
        content = str(r.get("content") or "").strip()
        if not content:
            continue
        tid = str(r.get("id") or i).strip() or str(i)
        while tid in seen:
            tid += "."
        seen.add(tid)
        status = r.get("status") if r.get("status") in STATUSES else "pending"
        prio = r.get("priority") if r.get("priority") in PRIORITIES else "medium"
        out.append({
            "id": tid, "content": content, "status": status,
            "priority": prio,
            "parent": str(r.get("parent") or "").strip(),
            "note": str(r.get("note") or "").strip(),
        })
    ids = {t["id"] for t in out}
    for t in out:
        if t["parent"] == t["id"] or t["parent"] not in ids:
            t["parent"] = ""
    return out


def _persist():
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(
            {"updated": time.time(), "todos": _items, "phase": _phase},
            ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
