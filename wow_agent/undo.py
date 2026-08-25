# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""改动快照：磁盘持久化。/undo 单步还原；同一轮任务用 cid 分组，可整轮回滚。"""

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


def push(path, existed, backup_text, cid=""):
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        fs = _files()
        seq = int(fs[-1].stem) + 1 if fs else 1
        data = {"seq": seq, "path": str(path), "existed": bool(existed),
                "backup": backup_text, "cid": cid}
        (DIR / f"{seq:04d}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")
        fs.append(DIR / f"{seq:04d}.json")
        while len(fs) > MAX_FILES:
            fs.pop(0).unlink(missing_ok=True)
    except OSError:
        pass


def _restore(d):
    """按单条快照还原文件，返回结果描述（[错误] 开头表示失败）。"""
    p = Path(d["path"])
    if d["existed"] and d["backup"] is not None:
        try:
            p.write_text(d["backup"], encoding="utf-8")
            return f"已还原 {p}（撤销 AI 的修改）"
        except OSError as e:
            return f"[错误] 还原 {p} 失败: {e}"
    try:
        p.unlink(missing_ok=True)
        return f"已删除新建的文件 {p}"
    except OSError as e:
        return f"[错误] 删除 {p} 失败: {e}"


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
    msg = _restore(d)
    if not msg.startswith("[错误]"):
        f.unlink(missing_ok=True)
    return msg


def group_depth(cid):
    """指定轮次 cid 名下尚未撤销的快照条数。"""
    if not cid:
        return 0
    n = 0
    for f in _files():
        try:
            if json.loads(f.read_text(encoding="utf-8")).get("cid") == cid:
                n += 1
        except (OSError, json.JSONDecodeError):
            continue
    return n


def undo_group(cid):
    """整轮回滚：逆序还原该轮全部快照，返回每条的还原描述。"""
    out = []
    if not cid:
        return out
    snaps = []
    for f in _files():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("cid") == cid:
            snaps.append((f, d))
    for f, d in reversed(snaps):
        msg = _restore(d)
        out.append(msg)
        if not msg.startswith("[错误]"):
            f.unlink(missing_ok=True)
    return out


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
