# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""长期记忆：跨目录跨会话的经验摘要存档，任何目录启动 wow 都能 /mem 调用。"""

import json
import os
import time
from pathlib import Path

ROOT = Path(os.environ.get("WOW_AGENT_HOME", str(Path.home()))) / ".wow-agent"
DIR = ROOT / "memory"


def listing(limit=50):
    if not DIR.exists():
        return []
    out = []
    for f in sorted(DIR.glob("*.json"), reverse=True)[:limit]:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def save(summary, title="", cwd="", model=""):
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        mid = ""
        for _ in range(50):
            cand = ("m" + time.strftime("%m%d-%H%M%S")
                    + f"-{time.time_ns():019d}")
            if not (DIR / f"{cand}.json").exists():
                mid = cand
                break
        if not mid:
            return ""
        data = {"id": mid, "title": title or "未命名记忆",
                "summary": summary, "cwd": cwd, "model": model,
                "created": time.time()}
        (DIR / f"{mid}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        return ""
    return mid


def delete(mid):
    try:
        (DIR / f"{mid}.json").unlink(missing_ok=True)
    except OSError:
        pass


MAX_MEMS = 30


def find_title(title):
    """按标题定位已有记忆（用于保存时去重更新）；空标题不参与。"""
    if not title:
        return None
    return next((d for d in listing() if d.get("title") == title), None)


def enforce_cap(limit=MAX_MEMS):
    """超过上限自动清理最旧的记忆，防止记忆库无限膨胀污染上下文。"""
    removed = 0
    for d in reversed(listing()[limit:]):
        delete(d["id"])
        removed += 1
    return removed
