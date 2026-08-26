---
title: Configuration
layout: docs
permalink: /config/
eyebrow: Reference
description: Every WOW_* environment variable, MCP servers and provider setup.
---

Config file: `~/.wow-agent.env` (permissions 600).

```bash
WOW_API_KEY=            # API key
WOW_BASE_URL=           # OpenAI-compatible endpoint
WOW_MODEL=              # model id
WOW_SAFE_MODE=1         # 0 disables sandbox (not recommended)
WOW_MAX_ITER=40         # max iterations per task
WOW_AUTO_COMPACT=55000  # auto-compact threshold (tokens)
WOW_LANGUAGE=en         # en | zh, default en
WOW_MODEL_CTX=128000    # model context length for estimates
WOW_CELL_ASPECT=2.0     # terminal cell aspect (logo scaling)
WOW_UPLOAD_GUARD=1      # egress protection switch
```

## MCP servers

`~/.wow-agent/mcp.json`:

```json
{
  "servers": {
    "fs": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fs", "/tmp"] }
  }
}
```

## Precedence

CLI flags → `~/.wow-agent.env` → project `.env` → built-in defaults.

Inspect at runtime: `/config`, `/config get WOW_MAX_ITER`, `/config set WOW_MAX_ITER 60` (session only).
