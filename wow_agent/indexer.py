# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""项目索引：一次扫描生成 文件树 + Python 符号表（ast），模型先查索引再精读，
省掉反复 find/grep 烧上下文。索引存 ~/.wow-agent/index/<proj>.json，不污染项目。"""

import ast
import hashlib
import json
import os
import time
from pathlib import Path

ROOT = Path(os.environ.get("WOW_AGENT_HOME", str(Path.home()))) / ".wow-agent"
DIR = ROOT / "index"
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist",
             "build", ".wow", ".idea", ".vscode", ".mypy_cache",
             ".pytest_cache", ".tox", "target"}
MAX_FILES = 5000
MAX_FILE_BYTES = 512 * 1024
SEARCH_MAX = 50


def _path(root):
    key = hashlib.md5(str(root).encode()).hexdigest()[:12]
    return DIR / f"{key}.json"


def _parse_py(p):
    """提取顶层/类内函数与类定义、import 模块名；语法错误返回占位符号。"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return [{"kind": "note", "name": "(无法解析)", "line": 1}]
    out = []

    def walk(nodes, prefix=""):
        for n in nodes:
            if isinstance(n, ast.ClassDef):
                out.append({"kind": "class",
                            "name": prefix + n.name, "line": n.lineno})
                walk(n.body, prefix + n.name + ".")
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append({"kind": "func",
                            "name": prefix + n.name, "line": n.lineno})
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    mod = getattr(n, "module", None) or a.name
                    out.append({"kind": "import",
                                "name": mod, "line": n.lineno})

    walk(tree.body)
    return out


def build(root="."):
    root = Path(root).expanduser().resolve()
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        parts = set(p.parts)
        if parts & SKIP_DIRS:
            continue
        if len(files) >= MAX_FILES:
            files.append({"path": "...[文件过多，索引已截断]", "size": 0,
                          "mtime": 0})
            break
        rel = str(p.relative_to(root))
        try:
            st = p.stat()
        except OSError:
            continue
        entry = {"path": rel, "size": st.st_size, "mtime": st.st_mtime}
        if (p.suffix == ".py" and st.st_size <= MAX_FILE_BYTES):
            entry["symbols"] = _parse_py(p)
        files.append(entry)
    data = {"built": time.time(), "root": str(root), "files": files}
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        _path(root).write_text(json.dumps(data, ensure_ascii=False),
                               encoding="utf-8")
    except OSError:
        pass
    return data


def load(root="."):
    try:
        return json.loads(_path(Path(root).expanduser().resolve())
                          .read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def ensure(root=".", max_age=3600):
    """索引缺失或比最新文件改动旧时自动重建；返回 (data, rebuilt)。"""
    d = load(root)
    if d and not d["files"]:
        return d, False
    newest = 0.0
    rootp = Path(root).expanduser().resolve()
    if d:
        for f in d["files"]:
            mtime = f.get("mtime") or 0
            if mtime > newest:
                newest = mtime
        stale = d.get("built", 0) < newest or \
            time.time() - d.get("built", 0) > max_age * 24
    else:
        stale = True
        for p in list(rootp.rglob("*.py"))[:200]:
            try:
                newest = max(newest, p.stat().st_mtime)
            except OSError:
                continue
    if stale or d is None:
        return build(root), True
    return d, False


def query(action="summary", q="", path="", root="."):
    data, rebuilt = ensure(root)
    if data is None:
        return "[错误] 项目索引不可用"
    files = [f for f in data["files"] if f.get("mtime")]
    head = (f"[索引 {data['root']} · {len(files)} 文件 · "
            f"{'刚重建' if rebuilt else '缓存命中'}]")
    if action == "rebuild":
        data = build(root)
        return f"[已重建] {len([f for f in data['files'] if f.get('mtime')])} 文件"
    if action == "search":
        kw = str(q).strip().lower()
        if not kw:
            return head + "\n[错误] search 需要 query 参数"
        hits = []
        for f in files:
            for s in f.get("symbols") or []:
                if kw in s["name"].lower():
                    hits.append(f"{f['path']}:{s['line']} "
                                f"{s['kind']} {s['name']}")
                    if len(hits) >= SEARCH_MAX:
                        break
            if len(hits) >= SEARCH_MAX:
                break
        return head + ("\n" + "\n".join(hits) if hits else "\n[无匹配]")
    if action == "file":
        f = next((f for f in files if f["path"] == path.strip()), None)
        if f is None:
            return head + f"\n[错误] 索引中没有 {path}"
        syms = "\n".join(f"{s['line']:>5} {s['kind']:<6} {s['name']}"
                         for s in f.get("symbols") or [])
        return head + f"\n{f['path']} ({f['size']}B)\n{syms or '(无符号)'}"
    # summary
    exts = {}
    dirs = {}
    nsym = 0
    for f in files:
        ext = Path(f["path"]).suffix or "(无后缀)"
        exts[ext] = exts.get(ext, 0) + 1
        top = f["path"].split("/", 1)[0] if "/" in f["path"] else "./"
        dirs[top] = dirs.get(top, 0) + 1
        nsym += len(f.get("symbols") or [])
    lines = [head,
             "扩展名: " + " ".join(f"{k}×{v}" for k, v in
                                   sorted(exts.items(),
                                          key=lambda x: -x[1])[:12]),
             "顶层目录: " + " ".join(f"{k}×{v}" for k, v in
                                     sorted(dirs.items(),
                                            key=lambda x: -x[1])[:12]),
             f"Python 符号共 {nsym} 个 · 用 action=search '关键词' 定位符号，"
             "action=file 看单文件结构"]
    return "\n".join(lines)
