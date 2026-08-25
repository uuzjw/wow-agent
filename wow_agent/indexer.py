# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""项目索引：一次扫描生成 文件树 + 多语言符号表，模型先查索引再精读，
省掉反复 find/grep 烧上下文。索引存 ~/.wow-agent/index/<proj>.json，不污染项目。"""

import ast
import hashlib
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(os.environ.get("WOW_AGENT_HOME", str(Path.home()))) / ".wow-agent"
DIR = ROOT / "index"
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist",
             "build", ".wow", ".idea", ".vscode", ".mypy_cache",
             ".pytest_cache", ".tox", "target", ".gradle", "vendor"}
MAX_FILES = 5000
MAX_FILE_BYTES = 512 * 1024
SEARCH_MAX = 50

# 语言配置：后缀 -> (语言名, 解析器函数名)
LANG_PARSERS = {
    ".py": ("python", "_parse_py"),
    ".js": ("javascript", "_parse_js_ts"),
    ".jsx": ("javascript", "_parse_js_ts"),
    ".ts": ("typescript", "_parse_js_ts"),
    ".tsx": ("typescript", "_parse_js_ts"),
    ".go": ("go", "_parse_go"),
    ".rs": ("rust", "_parse_rust"),
    ".c": ("c", "_parse_c_cpp"),
    ".h": ("c", "_parse_c_cpp"),
    ".cpp": ("cpp", "_parse_c_cpp"),
    ".cc": ("cpp", "_parse_c_cpp"),
    ".cxx": ("cpp", "_parse_c_cpp"),
    ".hpp": ("cpp", "_parse_c_cpp"),
    ".java": ("java", "_parse_java"),
    ".kt": ("kotlin", "_parse_kotlin"),
    ".rb": ("ruby", "_parse_ruby"),
    ".php": ("php", "_parse_php"),
    ".cs": ("csharp", "_parse_csharp"),
    ".swift": ("swift", "_parse_swift"),
    ".sh": ("shell", "_parse_shell"),
    ".py": ("python", "_parse_py"),
}

# 通用正则：用于没有专用解析器的语言
GENERIC_PATTERNS = {
    "function": re.compile(r"^\s*(?:async\s+)?(?:function|def|fn|func|func\s+\w+\s*\(|func\s+\w+\s*\w+\s*\()\s*(\w+)"),
    "class": re.compile(r"^\s*(?:class|struct|interface|trait|type)\s+(\w+)"),
    "import": re.compile(r"^\s*(?:import|include|require|use|from)\s+[\w./*]+"),
}


def _path(root):
    key = hashlib.md5(str(root).encode()).hexdigest()[:12]
    return DIR / f"{key}.json"


# ===== 语言专用解析器 =====

def _parse_py(p):
    """Python: ast 解析类/函数/import"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return [{"kind": "note", "name": "(无法解析)", "line": 1}]
    out = []

    def walk(nodes, prefix=""):
        for n in nodes:
            if isinstance(n, ast.ClassDef):
                out.append({"kind": "class", "name": prefix + n.name, "line": n.lineno})
                walk(n.body, prefix + n.name + ".")
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append({"kind": "func", "name": prefix + n.name, "line": n.lineno})
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    mod = getattr(n, "module", None) or a.name
                    out.append({"kind": "import", "name": mod, "line": n.lineno})

    walk(tree.body)
    return out


def _parse_js_ts(p):
    """JavaScript/TypeScript: 正则提取 class/function/import/export"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # import/export
        m = re.match(r"^\s*(?:import|export)\s+(?:.*\s+from\s+)?['\"]([^'\"]+)['\"]", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        # class
        m = re.match(r"^\s*(?:export\s+)?class\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        # function / arrow function
        m = re.match(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        # arrow function assigned to const/let/var
        m = re.match(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?\w*\)?\s*=>", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        # interface / type
        m = re.match(r"^\s*(?:export\s+)?(?:interface|type)\s+(\w+)", line)
        if m:
            out.append({"kind": "interface", "name": m.group(1), "line": i})
    return out


def _parse_go(p):
    """Go: 正则提取 func/type/import"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # import
        m = re.match(r'^\s*(?:import\s+(?:"([^"]+)"|\(([^)]+)\))', line)
        if m:
            mod = m.group(1) or m.group(2)
            out.append({"kind": "import", "name": mod, "line": i})
        # func
        m = re.match(r"^\s*func\s+(?:\(\w+\s+\w+\)\s+)?(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        # struct/interface
        m = re.match(r"^\s*type\s+(\w+)\s+(?:struct|interface)", line)
        if m:
            out.append({"kind": "type", "name": m.group(1), "line": i})
    return out


def _parse_rust(p):
    """Rust: 正则提取 fn/struct/enum/trait/impl/use/mod"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # use
        m = re.match(r"^\s*use\s+([\w:]+)", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        # fn
        m = re.match(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        # struct/enum/trait
        m = re.match(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)", line)
        if m:
            out.append({"kind": m.group(0).split()[1], "name": m.group(1), "line": i})
        # impl
        m = re.match(r"^\s*impl\s+(?:<\w+>)?\s*(\w+)", line)
        if m:
            out.append({"kind": "impl", "name": m.group(1), "line": i})
    return out


def _parse_c_cpp(p):
    """C/C++: 正则提取函数/类/结构体/宏/include"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # include
        m = re.match(r"^\s*#include\s+[<\"]([^>\"]+)[>\"]", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        # function
        m = re.match(r"^\s*(?:inline\s+)?(?:static\s+)?(?:const\s+)?\w+(?:\s*\*)?\s+(\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:;|\{)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        # class/struct
        m = re.match(r"^\s*(?:class|struct)\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
    return out


def _parse_java(p):
    """Java: 正则提取 class/interface/method/import"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*import\s+([\w.]+)", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:public\s+)?(?:abstract\s+)?(?:class|interface)\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*\(", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
    return out


def _parse_kotlin(p):
    """Kotlin: 正则提取 class/fun/import"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*import\s+([\w.]+)", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:class|interface|object|data\s+class)\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:fun|val|var)\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
    return out


def _parse_ruby(p):
    """Ruby: 正则提取 class/module/def/require"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*require\s+['\"]([^'\"]+)['\"]", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:class|module)\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        m = re.match(r"^\s*def\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
    return out


def _parse_php(p):
    """PHP: 正则提取 class/function/use/namespace"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*use\s+([\w\\]+)", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:abstract\s+)?class\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        m = re.match(r"^\s*function\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
    return out


def _parse_csharp(p):
    """C#: 正则提取 class/interface/method/using/namespace"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*using\s+([\w.]+)", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:public\s+)?(?:class|interface|struct)\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
    return out


def _parse_swift(p):
    """Swift: 正则提取 class/struct/func/import"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*import\s+(\w+)", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:class|struct|protocol)\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:func|var|let)\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
    return out


def _parse_shell(p):
    """Shell: 正则提取 function/alias/export/source"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*(?:function\s+)?(\w+)\s*\(\)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:alias|export)\s+(\w+)", line)
        if m:
            out.append({"kind": "var", "name": m.group(1), "line": i})
    return out


# 通用回退：简单正则提取
def _parse_generic(p, lang):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s*(?:import|include|require|use)\s+[\w./*]+", line)
        if m:
            out.append({"kind": "import", "name": line.strip()[:80], "line": i})
        m = re.match(r"^\s*(?:class|struct|interface|trait|type)\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        m = re.match(r"^\s*(?:function|def|fn|func)\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
    return out


def parse_file(p):
    """统一入口：根据后缀分派解析器"""
    suffix = p.suffix.lower()
    if suffix == ".py":
        return _parse_py(p)
    elif suffix in (".js", ".jsx", ".ts", ".tsx"):
        return _parse_js_ts(p)
    elif suffix == ".go":
        return _parse_go(p)
    elif suffix == ".rs":
        return _parse_rust(p)
    elif suffix in (".c", ".h", ".cpp", ".cc", ".cxx", ".hpp"):
        return _parse_c_cpp(p)
    elif suffix == ".java":
        return _parse_java(p)
    elif suffix == ".kt":
        return _parse_kotlin(p)
    elif suffix == ".rb":
        return _parse_ruby(p)
    elif suffix == ".php":
        return _parse_php(p)
    elif suffix == ".cs":
        return _parse_csharp(p)
    elif suffix == ".swift":
        return _parse_swift(p)
    elif suffix == ".sh":
        return _parse_shell(p)
    else:
        return _parse_generic(p, p.suffix)


def _parse_js_ts(p):
    """JavaScript/TypeScript: 正则提取 class/function/import/export"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [{"kind": "note", "name": "(无法读取)", "line": 1}]
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # import/export
        m = re.match(r"^\s*(?:import|export)\s+(?:.*\s+from\s+)?['\"]([^'\"]+)['\"]", line)
        if m:
            out.append({"kind": "import", "name": m.group(1), "line": i})
        # class
        m = re.match(r"^\s*(?:export\s+)?class\s+(\w+)", line)
        if m:
            out.append({"kind": "class", "name": m.group(1), "line": i})
        # function / arrow function
        m = re.match(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        # arrow function assigned to const/let/var
        m = re.match(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?\w*\)?\s*=>", line)
        if m:
            out.append({"kind": "func", "name": m.group(1), "line": i})
        # interface / type
        m = re.match(r"^\s*(?:export\s+)?(?:interface|type)\s+(\w+)", line)
        if m:
            out.append({"kind": "interface", "name": m.group(1), "line": i})
    return out


# ===== 通用工具 =====

def _path(root):
    key = hashlib.md5(str(root).encode()).hexdigest()[:12]
    return DIR / f"{key}.json"


# ===== 主流程 =====

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
        if (p.suffix in LANG_PARSERS and st.st_size <= MAX_FILE_BYTES):
            entry["symbols"] = parse_file(p)
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
        for p in list(rootp.rglob("*"))[:200]:
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
    lang_counts = {}
    for f in files:
        ext = Path(f["path"]).suffix or "(无后缀)"
        exts[ext] = exts.get(ext, 0) + 1
        top = f["path"].split("/", 1)[0] if "/" in f["path"] else "./"
        dirs[top] = dirs.get(top, 0) + 1
        symbols = f.get("symbols") or []
        nsym += len(symbols)
        for s in symbols:
            lang = s.get("lang", "未知")
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    lines = [head,
             "扩展名: " + " ".join(f"{k}×{v}" for k, v in
                                     sorted(exts.items(),
                                            key=lambda x: -x[1])[:12]),
             "顶层目录: " + " ".join(f"{k}×{v}" for k, v in
                                     sorted(dirs.items(),
                                            key=lambda x: -x[1])[:12]),
             f"符号共 {nsym} 个" + (f" (Python {lang_counts.get('python', 0)})" if lang_counts.get('python', 0) else "") +
             " · 用 action=search '关键词' 定位符号，"
             "action=file 看单文件结构"]
    return "\n".join(lines)