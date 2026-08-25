# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""冒烟测试：python3 tests_smoke.py（不需要网络和 API key）。"""

import os
import sys
import tempfile
from pathlib import Path

os.environ["WOW_AGENT_HOME"] = tempfile.mkdtemp(prefix="wow-test-")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wow_agent import todo, tools  # noqa: E402
from wow_agent import memory as mem  # noqa: E402
from wow_agent import session as sess  # noqa: E402
from wow_agent.subagent import SUB_TOOLS  # noqa: E402
from wow_agent.ui import render_todo_panel, UI  # noqa: E402


def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        sys.exit(1)


todo.set_all([
    {"id": "1", "content": "搭骨架", "status": "completed", "priority": "high"},
    {"id": "2", "content": "实现功能", "status": "in_progress",
     "priority": "medium", "parent": "", "note": "核心逻辑写了一半"},
    {"id": "2.1", "content": "子步骤A", "status": "pending", "priority": "low",
     "parent": "2"},
    {"id": "3", "content": "收尾", "status": "pending", "priority": "high"},
])
rows = todo.sorted_tree()
check("树排序：高优先级根在前", [r[0]["id"] for r in rows][:2] == ["1", "3"])
check("树嵌套：2.1 挂在 2 下且深度+1",
      any(r[0]["id"] == "2.1" and r[1] == 1 for r in rows))
total, done, prog = todo.counts()
check("计数", (total, done, prog) == (4, 1, 1))

receipt = tools.execute("todo_write", {"todos": [
    {"id": "1", "content": "唯一任务", "status": "completed",
     "priority": "high", "note": "搞定"}]})
check("todo_write 工具回执", "已更新" in receipt)
check("todo_write 已生效", todo.counts() == (1, 1, 0))
bad = tools.execute("todo_write", {"todos": [{"content": "", "status": "x"}]})
check("非法条目被过滤", todo.counts()[0] == 0)

panel = render_todo_panel()
check("面板可渲染", panel is not None)

check("task/write 工具对子代理禁用（白名单）",
      "task" not in SUB_TOOLS and "write_file" not in SUB_TOOLS
      and "edit_file" not in SUB_TOOLS)

is_up = tools.is_upload_like
check("上传识别 git push", is_up("cd repo && git push origin main"))
check("上传识别 curl POST", is_up("curl -d @f.json https://api.x.com/up"))
check("上传识别 scp/ssh", is_up("scp a.txt host:/tmp") and is_up("ssh host"))
check("上传识别 npm publish", is_up("npm publish --access public"))
check("上传识别 rsync 远程", is_up("rsync -av ./dir backup@nas:/bak"))
check("下载放行 curl GET", not is_up("curl https://example.com/docs"))
check("下载放行 pip install", not is_up("pip install requests"))
check("查看类放行 ls/grep", not is_up("ls -la | grep py"))

from wow_agent import config as cfg  # noqa: E402
check("外传防护默认开", cfg.UPLOAD_GUARD is True)
cfg.set_upload_guard(False)
check("/safe 开关可切换", cfg.UPLOAD_GUARD is False)
cfg.set_upload_guard(True)

pids = list(cfg.PROVIDERS)
check("服务商扩容 >= 16 家", len(pids) >= 16)
ok = all(p.get("name") and p.get("base_url") for p in cfg.PROVIDERS.values())
urls = [p["base_url"] for p in cfg.PROVIDERS.values()]
check("服务商结构完整且 base_url 无重复",
      ok and len(urls) == len(set(urls)))
zen = cfg.PROVIDERS["zen"]
check("Zen 预置 ox alpha (x-preview-f-free)",
      "x-preview-f-free" in zen["models"])
broken = {"deepseek-v4-flash-free", "muse-spark-1.2-contributor-free"}
check("Zen 预置已剔除实测不可用模型",
      not (set(zen["models"]) & broken))
check("fetch_models 坏地址优雅返回 None",
      cfg.fetch_models("http://127.0.0.1:1/v1", "k", timeout=1) is None)
live = cfg.fetch_models(zen["base_url"], "", timeout=10)
check(f"Zen /models 在线可拉取({len(live) if live else 0} 个)", bool(live))
check("别名解析 ox alpha",
      cfg.resolve_model("ox alpha") == "x-preview-f-free"
      and cfg.resolve_model("Ox") == "x-preview-f-free"
      and cfg.resolve_model("deepseek-chat") == "deepseek-chat")

mid = mem.save("测试摘要内容", title="标题X", cwd="/tmp", model="m1")
row = next((d for d in mem.listing() if d["id"] == mid), None)
check("记忆保存/读取", row and row["title"] == "标题X")
check("记忆列表", any(d["summary"] == "测试摘要内容" for d in mem.listing()))
mem.delete(mid)
check("记忆删除", all(d["id"] != mid for d in mem.listing()))

base = [mem.save(f"s{i}", title=f"c{i}") for i in range(mem.MAX_MEMS)]
mem.save("旧的多余项", title="extra-old")
mem.save("新的多余项", title="extra-new")
removed = mem.enforce_cap()
check("记忆超限自动清理最旧",
      removed == 2 and len(mem.listing()) == mem.MAX_MEMS
      and all(d["id"] != base[0] for d in mem.listing()))
check("同名记忆可定位去重",
      mem.find_title("extra-new") is not None
      and mem.find_title("") is None)
for d in mem.listing():
    mem.delete(d["id"])

big = Path(tempfile.mkdtemp(prefix="wow-read-")) / "big.txt"
big.write_text("\n".join(f"line{i}" for i in range(1, 5001)), encoding="utf-8")
r1 = tools.execute("read_file", {"path": str(big)})
check("read_file 默认截断并提示续读",
      "共 5000 行" in r1 and "显示第 1-2000 行" in r1 and "offset=2001" in r1)
r2 = tools.execute("read_file",
                   {"path": str(big), "offset": 2001, "limit": 100})
check("read_file 分块读取",
      r2.splitlines()[1] == "line2001" and "显示第 2001-2100 行" in r2)
r3 = tools.execute("read_file", {"path": str(big), "offset": 4999, "limit": 99})
check("read_file 越界截到末尾不炸",
      "显示第 4999-5000 行" in r3 and "续读" not in r3)

sid = sess.new_id()
sess.save(sid, [{"role": "user", "content": "hi"}], {}, todos=[{"content": "a"}])
d = sess.load(sid)
check("会话存档包含 todos", d["todos"][0]["content"] == "a")

import json  # noqa: E402

todo.set_all([{"id": "1", "content": "a", "status": "pending"}])
todo.save(sid)
todo.reset()
check("reset 后清单为空", todo.items() == [])
raw = json.loads((todo.ROOT / f"todo-{sid}.json").read_text())
todo.set_all(raw)
check("todo 持久化 roundtrip", todo.items()[0]["content"] == "a")

ui = UI()
ui.set_todos([{"id": "1", "content": "任务", "status": "in_progress"}])
check("UI set_todos 同步", ui.todo_badge() == "☑0/1")

from wow_agent.agent import est_tokens  # noqa: E402
check("token 估算仍工作", est_tokens([{"role": "user", "content": "hello"}]) > 0)

# ---- v0.6.0 整轮分组回滚 ----
from wow_agent import undo as und  # noqa: E402

tmpu = Path(tempfile.mkdtemp(prefix="wow-undo-"))
fA = tmpu / "a.txt"
fB = tmpu / "b.txt"
fC = tmpu / "c.txt"
fA.write_text("orig-a")
fC.write_text("keep")
und.push(str(fA), True, "orig-a", cid="t1")
fA.write_text("mod-a")
und.push(str(fB), False, None, cid="t1")
fB.write_text("new-b")
und.push(str(fC), True, "keep")
check("整轮快照计数", und.group_depth("t1") == 2)
und.undo_group("t1")
check("整轮回滚还原+删新建",
      fA.read_text() == "orig-a" and not fB.exists())
check("整轮回滚不误伤他轮", fC.read_text() == "keep"
      and und.group_depth("t1") == 0)
und.undo()
check("单步 /undo 兼容", fC.read_text() == "keep" and und.depth() == 0)

# ---- v0.6.0 任务状态机 ----
todo.reset()
check("状态机默认规划", todo.phase() == "planning")
receipt = tools.execute("todo_write",
                        {"todos": [{"content": "x"}], "phase": "executing"})
check("todo_write 切阶段", todo.phase() == "executing" and "执行中" in receipt)
check("非法阶段拒绝", not todo.set_phase("bogus"))
tools.execute("todo_write",
              {"todos": [{"content": "x"}], "phase": "verifying"})
check("阶段推进到验证", todo.phase() == "verifying")
todo.reset()
check("reset 回规划", todo.phase() == "planning")

# ---- v0.6.0 项目索引 ----
from wow_agent import indexer  # noqa: E402

proj = Path(tempfile.mkdtemp(prefix="wow-idx-"))
(proj / "pkg").mkdir()
(proj / "pkg" / "__init__.py").write_text("")
(proj / "pkg" / "mod.py").write_text(
    "import os\n\nclass Alpha:\n    def go(self):\n        pass\n"
    "\n\ndef beta():\n    return 1\n")
(proj / "readme.md").write_text("# hi\n")
d = indexer.build(proj)
check("索引构建文件数", sum(1 for f in d["files"] if f.get("mtime")) == 3)
r = indexer.query(action="search", q="alpha", root=str(proj))
check("索引符号搜索", "pkg/mod.py" in r and "class Alpha" in r)
r = indexer.query(action="file", path="pkg/mod.py", root=str(proj))
check("索引单文件结构", "func" in r and "Alpha.go" in r and "beta" in r)
r = indexer.query(action="summary", root=str(proj))
check("索引概览", "扩展名" in r and "Python 符号" in r)

# ---- v0.6.0 MCP stdio 客户端（假服务器回路）----
FAKE_MCP = """import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    m = json.loads(line)
    r = {}
    if m.get("method") == "initialize":
        r = {"jsonrpc": "2.0", "id": m["id"], "result": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "serverInfo": {"name": "fake"}}}
    elif m.get("method") == "tools/list":
        r = {"jsonrpc": "2.0", "id": m["id"], "result": {"tools": [
            {"name": "echo", "description": "回声",
             "inputSchema": {"type": "object",
                             "properties": {"text": {"type": "string"}}}}]}}
    elif m.get("method") == "tools/call":
        t = m["params"].get("arguments", {}).get("text", "")
        r = {"jsonrpc": "2.0", "id": m["id"], "result": {
            "content": [{"type": "text", "text": "ECHO:" + t}]}}
    if r:
        print(json.dumps(r), flush=True)
"""
from wow_agent import mcp as mcpx  # noqa: E402

srv_py = Path(tempfile.mkdtemp(prefix="wow-mcp-")) / "fake_server.py"
srv_py.write_text(FAKE_MCP)
srv = mcpx.Server("fake", {"command": sys.executable,
                           "args": [str(srv_py)]})
srv.start()
tl = srv.list_tools()
check("MCP initialize+list_tools", [t["name"] for t in tl] == ["echo"])
out = srv.call("echo", {"text": "wow"})
check("MCP tools/call 回声", out == "ECHO:wow")
srv.stop()

print("\nALL SMOKE TESTS PASSED")
