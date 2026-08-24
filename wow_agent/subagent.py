"""只读子代理：全新干净上下文 + 受限只读工具，调研后只把结论带回主对话。"""

import json

from openai import OpenAI

from . import config
from .tools import TOOLS_SCHEMA, execute

SUB_TOOLS = ("read_file", "glob_files", "grep_search", "run_bash")
SCHEMA = [t for t in TOOLS_SCHEMA if t["function"]["name"] in SUB_TOOLS]
RESULT_MAX = 8000

SUB_SYSTEM = (
    "你是 wow-agent 派出的调研子代理，在全新上下文里只读调研，"
    "结论会回传给主代理执行，所以只汇报结论，不执行修改。\n"
    "规则:\n"
    "- 只允许 read_file / glob_files / grep_search 和查看类 bash 命令"
    "（ls/cat/wc/find 等），严禁写入、修改、删除、安装、联网\n"
    "- 搜索要有的放矢：先 glob/grep 定位，再精读关键文件，不要逐个翻\n"
    f"- 最多 {config.SUB_ITER} 轮，在轮次内完成调研\n"
    "- 调研完成后，最后一条回复只输出结论："
    "关键发现 → 涉及文件:行号 → 对主任务的建议，500 字以内")


def run(prompt, ui, description=""):
    from .agent import _stream_assistant

    client = OpenAI(api_key=config.API_KEY or "none",
                    base_url=config.BASE_URL)
    messages = [{"role": "system", "content": SUB_SYSTEM},
                {"role": "user", "content": prompt}]
    head = " ".join((description or prompt).split())[:60]
    ui.console.print(f"  [magenta]┌ 子代理[/magenta] [dim]{head}[/dim]")
    final = ""
    try:
        for it in range(config.SUB_ITER):
            msg = _stream_assistant(client, messages, ui, SCHEMA,
                                    f"子代理调研 {it + 1}/{config.SUB_ITER}")
            calls = msg.get("tool_calls")
            if not calls:
                final = (msg.get("content") or "").strip()
                break
            for call in calls:
                name = call["function"]["name"]
                raw = call["function"]["arguments"]
                ui.tool_start(name, raw)
                if name not in SUB_TOOLS:
                    result = "[错误] 子代理仅限只读工具"
                else:
                    try:
                        result = execute(name, json.loads(raw or "{}"))
                    except Exception as e:
                        result = f"[工具执行出错] {e}: {type(e).__name__}"
                ui.tool_result(name, result, 0.0)
                messages.append({"role": "tool",
                                 "tool_call_id": call["id"],
                                 "content": result[:20000]})
        else:
            final = (msg.get("content") or "").strip()
    finally:
        ui.console.print("  [magenta]└ 子代理结束[/magenta]")
    if not final:
        final = "（子代理没有返回结论，已达轮次上限）"
    return final[:RESULT_MAX]
