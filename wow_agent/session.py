# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""会话保存与恢复：每轮对话后自动存档，/resume 恢复继续聊。"""

import json
import os
import time
from pathlib import Path

ROOT = Path(os.environ.get("WOW_AGENT_HOME", str(Path.home()))) / ".wow-agent"
DIR = ROOT / "sessions"


def new_id():
    return time.strftime("%Y%m%d-%H%M%S")


def _path(sid):
    return DIR / f"{sid}.json"


def save(sid, messages, meta, todos=None):
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        data = {"id": sid, "updated": time.time(), "meta": meta,
                "messages": messages, "todos": todos or []}
        _path(sid).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def load(sid):
    return json.loads(_path(sid).read_text(encoding="utf-8"))


def listing(limit=10):
    if not DIR.exists():
        return []
    out = []
    for f in sorted(DIR.glob("*.json"), reverse=True)[:limit]:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        first = ""
        for m in d.get("messages", []):
            c = m.get("content") or ""
            if m.get("role") == "user" and not c.startswith("["):
                first = " ".join(c.split())[:42]
                break
        n = len(d.get("messages", []))
        out.append((d["id"], d.get("meta", {}).get("model", "?"), n, first))
    return out
