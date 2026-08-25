# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""冒烟测试：python3 tests_smoke.py（不需要网络和 API key）。"""

import os
import sys
import tempfile

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

print("\nALL SMOKE TESTS PASSED")
