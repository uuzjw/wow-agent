---
title: Developer Tutorials
layout: docs
permalink: /tutorials/
eyebrow: Developer
description: Hands-on tutorials for extending wow-agent — custom tools, model providers, MCP servers, sub-agents and contributing.
---

wow-agent is built to be extended. Every layer exposes a clean extension point. Pick your path:

## Learning paths

| I want to… | Tutorial | Difficulty |
|---|---|---|
| Give the agent a new ability (e.g. deploy, query internal API) | [Custom Tools](/tutorials/custom-tools/) | ★☆☆ |
| Connect a model provider that isn't built in | [Add a Provider](/tutorials/add-provider/) | ★☆☆ |
| Wire up external capabilities via MCP (filesystem, GitHub, DBs) | [MCP Servers](/tutorials/mcp-servers/) | ★★☆ |
| Understand & build isolated research/review agents | [Sub-agents](/tutorials/subagents/) | ★★☆ |
| Fix a bug or ship a feature in wow-agent itself | [Contributing](/tutorials/contributing/) | ★★☆ |

## The 30-second mental model

```text
You ──▶ Agent Brain (plans, decides)
           │ calls
           ▼
        TOOLS  ← everything the agent can DO lives here
           │
     ┌─────┼──────┐
     ▼     ▼      ▼
   built-in custom  MCP     ← your extension points
   (read/edit/ (your    (external
    shell/…)  schema)  servers)
```

Three ways in, by effort:

1. **MCP server** — zero wow-agent code; run any standard MCP server
2. **Custom tool** — ~30 lines of Python in `tools.py`
3. **Core contribution** — modify the agent itself; see [Contributing](/tutorials/contributing/)

## Ground rules for extensions

- Tools must declare a **safety level** (`safe` / `modify` / `destructive`) — the safety system enforces it
- All I/O goes through the tool layer so snapshots and logging cover your code too
- Prefer JSON-Schema-validated parameters; the model fills them, validation protects you

Start with [Custom Tools](/tutorials/custom-tools/) — most people are done in 15 minutes.
