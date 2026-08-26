---
title: MCP Integration
layout: docs
permalink: /tools/mcp/
eyebrow: Tools
description: Extend the agent with Model Context Protocol servers — filesystem, GitHub, databases and your own.
---

## Configure

`~/.wow-agent/mcp.json`:

```json
{
  "servers": {
    "fs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fs", "/tmp"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_xxx" }
    }
  }
}
```

## How it works

On startup the agent launches each server, discovers its tools and registers them as `mcp_<server>_<tool>`. From then on the model calls them like any built-in tool.

## Security

- Servers inherit the agent's network sandbox
- Scope filesystem servers to narrow directories
- Pin versions: `server-github@1.2.3`

## Debug

```bash
/debug mcp        # server status (running/failed)
/mcp refresh      # reconnect + rediscover tools
```
