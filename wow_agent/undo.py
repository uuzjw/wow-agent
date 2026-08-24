"""改动快照：磁盘持久化，跨重启也能 /undo 逐步还原 AI 的文件修改。"""

import json
import os
from pathlib import Path

ROOT = Path(os.environ.get("WOW_AGENT_HOME", str(Path.home()))) / ".wow-agent"
DIR = ROOT / "undo"
MAX_FILES = 50


def _files():
    if not DIR.exists():
        return []
    return sorted(DIR.glob("*.json"))


def push(path, existed, backup_text):
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        fs = _files()
        seq = int(fs[-1].stem) + 1 if fs else 1
        data = {"seq": seq, "path": str(path), "existed": bool(existed),
                "backup": backup_text}
        (DIR / f"{seq:04d}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")
        fs.append(DIR / f"{seq:04d}.json")
        while len(fs) > MAX_FILES:
            fs.pop(0).unlink(missing_ok=True)
    except OSError:
        pass


def undo():
    fs = _files()
    if not fs:
        return None
    f = fs[-1]
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        f.unlink(missing_ok=True)
        return None
    p = Path(d["path"])
    if d["existed"] and d["backup"] is not None:
        try:
            p.write_text(d["backup"], encoding="utf-8")
            msg = f"已还原 {p}（撤销 AI 的修改）"
        except OSError as e:
            return f"[错误] 还原 {p} 失败: {e}"
    else:
        try:
            p.unlink(missing_ok=True)
            msg = f"已删除新建的文件 {p}"
        except OSError as e:
            return f"[错误] 删除 {p} 失败: {e}"
    f.unlink(missing_ok=True)
    return msg


def depth():
    return len(_files())


def recent(n=5):
    out = []
    for f in reversed(_files()[-n:]):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8"))["path"])
        except (OSError, json.JSONDecodeError, KeyError):
            continue
    return out
