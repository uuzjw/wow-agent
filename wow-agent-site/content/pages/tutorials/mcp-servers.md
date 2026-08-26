---
title: MCP Servers
layout: docs
permalink: /tutorials/mcp-servers/
eyebrow: Developer Tutorial
description: Extend wow-agent with Model Context Protocol servers — filesystem, GitHub, databases, or your own — with zero agent code.
---

MCP (Model Context Protocol) is a standard for exposing **tools** and **resources** to LLM agents. wow-agent speaks it natively: configure a server once, and its tools appear alongside built-ins.

## Step 1 — Configure

Create `~/.wow-agent/mcp.json`:

```json
{
  "servers": {
    "fs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/me/projects"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_xxx" }
    }
  }
}
```

Each server = a process command + args + optional env. wow-agent starts them on launch.

## Step 2 — Verify discovery

```text
You > /debug mcp
  fs      RUNNING   tools: read_file, write_file, list_directory, …
  github  RUNNING   tools: create_issue, get_pull_request, …

You > /debug tools          # mcp_fs__read_file etc. now listed
```

Tools are namespaced `mcp_<server>__<tool>` so they never collide with built-ins.

## Step 3 — Use it

Just ask naturally — the model sees the tool schemas:

```text
You > list open issues in uuzjw/wow-agent labeled "bug"
You > read /home/me/projects/notes/roadmap.md and summarize
```

## Write your own MCP server (Python)

```python
# my_server.py  —  pip install "mcp[cli]"
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("team-tools")

@mcp.tool()
def oncall_schedule() -> str:
    """Return this week's on-call engineer."""
    return "alice (Mon-Wed), bob (Thu-Fri)"

@mcp.tool()
def query_status(service: str) -> str:
    """Query internal status page for a service."""
    return f"{service}: all systems nominal"

if __name__ == "__main__":
    mcp.run()
```

Register it:

```json
{
  "servers": {
    "team": { "command": "python", "args": ["/path/to/my_server.py"] }
  }
}
```

## Security model

- MCP servers **inherit the agent's network sandbox** — a malicious server can't phone home
- Filesystem servers only see paths you pass in `args` — mount narrowly
- Tool calls still pass the safety system (`destructive` confirmations included)
- Pin versions for supply-chain safety: `server-github@1.2.3`

## Operations

```bash
/debug mcp          # status per server (running / failed + stderr)
/mcp refresh        # restart servers & rediscover tools
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| server FAILED at startup | run its command manually; read stderr |
| tools not appearing | `/mcp refresh`; check `npx` availability |
| slow startup | drop `-y` heavy packages you don't use; pin versions for cache |
