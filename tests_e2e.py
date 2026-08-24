"""端到端模拟：假 LLM 流式返回 → todo_write → task(打桩) → 最终回答。"""

import os
import sys
import tempfile
from types import SimpleNamespace as NS

os.environ["WOW_AGENT_HOME"] = tempfile.mkdtemp(prefix="wow-e2e-")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wow_agent import agent, todo  # noqa: E402
from wow_agent.ui import UI  # noqa: E402


def delta(content=None, tcs=None):
    d = NS(content=content, tool_calls=tcs)
    return NS(choices=[NS(delta=d, finish_reason=None)])


def tc_chunk(idx, name):
    fn = NS(name=name, arguments='{"todos":[{"content":"调研","status":"in_progress","priority":"high"}]}'
            if name == "todo_write" else '{"description":"查代码","prompt":"看看结构"}')
    call = NS(index=idx, id="c1", type="function", function=fn)
    return delta(tcs=[call])


class FakeCompletions:
    def __init__(self, script):
        self.script = iter(script)

    def create(self, **kw):
        return next(self.script)


def make_client(script):
    return NS(chat=NS(completions=FakeCompletions(script)))


agent.run_subtask = lambda prompt, ui, description="": \
    f"子代理报告: 已调研 [{prompt}]"

messages = [{"role": "system", "content": agent.system_prompt("/tmp")}]
script = [
    [tc_chunk(0, "todo_write")],
    [delta(content="派出子代理调研\n"), tc_chunk(0, "task")],
    [delta(content="结论：一切就绪")],
]
client = make_client(script)
ui = UI()
done, stats = agent.run_turn(client, messages, ui)

assert done, "循环未正常收尾"
assert stats["turns"] == 3, stats
assert any(m.get("role") == "tool" and "子代理报告" in m["content"]
           for m in messages), "task 结果未回填"
assert todo.items() and todo.items()[0]["status"] == "in_progress", "todo 未生效"
assert "[长期记忆" not in "".join(str(m) for m in messages)
print("E2E PASS:", stats, "| todos =", todo.counts())
