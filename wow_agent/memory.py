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
    mid = "m" + time.strftime("%m%d-%H%M%S")
    try:
        DIR.mkdir(parents=True, exist_ok=True)
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
