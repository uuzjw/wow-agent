# Copyright (c) 2026 uuzjw. MIT License.
# wow-agent - 独立开发的终端编码 Agent · https://github.com/uuzjw/wow-agent

"""MCP stdio 客户端：把外部 MCP Server 的工具桥接进 wow 的工具表。

配置文件 ~/.wow-agent/mcp.json：
{
  "servers": {
    "fs": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-fs", "/tmp"]}
  }
}
桥接后的工具名形如 mcp__<server>__<tool>，与内置工具一起下发给模型。
MCP Server 由用户显式配置，视为可信程序，不受断网沙盒约束（独立进程）。"""

import atexit
import itertools
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

from . import __version__

CONF = Path(os.environ.get("WOW_AGENT_HOME", str(Path.home()))
            ) / ".wow-agent" / "mcp.json"
PROTO_VERSION = "2024-11-05"
RPC_TIMEOUT = 30
CALL_TIMEOUT = 180
_ids = itertools.count(1)


class McpError(RuntimeError):
    pass


class Server:
    """一个 MCP stdio Server 进程：换行分隔 JSON-RPC，后台线程收包。"""

    def __init__(self, name, cfg):
        self.name = name
        self.cfg = cfg
        self.proc = None
        self.q = queue.Queue()
        self.tools = []

    def _reader(self):
        try:
            for line in self.proc.stdout:
                line = line.strip()
                if line:
                    self.q.put(line)
        except (OSError, ValueError):
            pass
        self.q.put(None)

    def start(self):
        cmd = [self.cfg["command"], *self.cfg.get("args", [])]
        env = dict(os.environ)
        env.update(self.cfg.get("env") or {})
        try:
            self.proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, env=env)
        except OSError as e:
            raise McpError(f"[{self.name}] 无法启动 {cmd[0]}: {e}")
        threading.Thread(target=self._reader, daemon=True).start()
        self.rpc("initialize", {
            "protocolVersion": PROTO_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "wow-agent", "version": __version__},
        })
        self.notify("notifications/initialized")
        return True

    def notify(self, method):
        if not self.proc:
            return
        try:
            self.proc.stdin.write(
                json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError):
            pass

    def rpc(self, method, params, timeout=RPC_TIMEOUT):
        mid = next(_ids)
        req = {"jsonrpc": "2.0", "id": mid, "method": method,
               "params": params}
        try:
            self.proc.stdin.write(json.dumps(req) + "\n")
            self.proc.stdin.flush()
        except (OSError, ValueError) as e:
            raise McpError(f"[{self.name}] 写入失败: {e}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            left = max(0.05, deadline - time.time())
            try:
                item = self.q.get(timeout=left)
            except queue.Empty:
                break
            if item is None:
                raise McpError(f"[{self.name}] 服务进程已退出")
            try:
                msg = json.loads(item)
            except json.JSONDecodeError:
                continue
            if isinstance(msg, dict) and msg.get("id") == mid:
                if "error" in msg:
                    raise McpError(f"[{self.name}] {method}: "
                                   f"{msg['error']}")
                return msg.get("result")
        raise McpError(f"[{self.name}] {method} 响应超时（{timeout}s）")

    def list_tools(self):
        r = self.rpc("tools/list", {})
        self.tools = (r.get("tools") or []
                      if isinstance(r, dict) else [])
        return self.tools

    def call(self, tool, args):
        r = self.rpc("tools/call", {"name": tool, "arguments": args},
                     timeout=CALL_TIMEOUT)
        parts = []
        if isinstance(r, dict):
            for c in r.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "text":
                    parts.append(str(c.get("text", "")))
            text = "\n".join(p for p in parts if p)
            if r.get("isError"):
                return f"[错误] {text or 'MCP 工具报告失败'}"
            return text or "(无内容返回)"
        return str(r)

    def stop(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
            except OSError:
                pass
            self.proc = None


_servers = {}
_loaded = False


def _conf():
    try:
        d = json.loads(CONF.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    servers = d.get("servers") if isinstance(d, dict) else None
    return servers if isinstance(servers, dict) else {}


def ensure_loaded():
    """懒加载：首次用到 MCP 时连接全部已配置 Server，失败的静默跳过。"""
    global _loaded
    if _loaded:
        return
    _loaded = True
    for name, cfg in _conf().items():
        if not isinstance(cfg, dict) or not cfg.get("command"):
            continue
        srv = Server(name, cfg)
        try:
            srv.start()
            srv.list_tools()
            _servers[name] = srv
        except Exception:
            srv.stop()


def status():
    ensure_loaded()
    return {name: [t["name"] for t in s.tools]
            for name, s in _servers.items()}


def schemas():
    """MCP 工具 schema 列表（并入主对话工具表）；未配置时为空。"""
    out = []
    for name, srv in status().items():
        for t in srv.tools:
            out.append({
                "type": "function",
                "function": {
                    "name": f"mcp__{name}__{t['name']}",
                    "description": (f"[MCP:{name}] "
                                    f"{t.get('description') or t['name']}"),
                    "parameters": (t.get("inputSchema")
                                   or {"type": "object", "properties": {}}),
                },
            })
    return out


def execute(fullname, args):
    _, _, sname, tname = fullname.split("__", 3)
    srv = _servers.get(sname)
    if srv is None:
        return f"[错误] MCP Server 未连接: {sname}"
    try:
        return srv.call(tname, args)
    except Exception as e:
        return f"[工具执行出错] MCP {sname}/{tname}: {e}"


@atexit.register
def _shutdown():
    for s in _servers.values():
        s.stop()
