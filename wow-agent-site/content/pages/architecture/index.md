---
title: Architecture
layout: docs
permalink: /architecture/
eyebrow: Architecture
description: Four layers — brain, tools, models, safety — and how they talk to each other.
---

```text
┌──────────────────────────────────────────────┐
│ Layer 1 · Agent Brain                        │
│ planning · state machine · sub-agents        │
└──────────────┬───────────────────────────────┘
┌──────────────▼───────────────────────────────┐
│ Layer 2 · Developer Tools                    │
│ file CRUD · diff/undo · code index           │
└──────────────┬───────────────────────────────┘
┌──────────────▼───────────────────────────────┐
│ Layer 3 · Model Ecosystem                    │
│ cloud 16+ providers · local Ollama/LM Studio │
└──────────────┬───────────────────────────────┘
┌──────────────▼───────────────────────────────┐
│ Layer 4 · Safety System                      │
│ sandbox · egress guard · confirm · rollback  │
└──────────────────────────────────────────────┘
```

## Module map

```
wow_agent/
├── agent.py      # core loop + state machine
├── cli.py        # entry point, commands
├── config.py     # providers, env
├── indexer.py    # AST code index
├── tools.py      # tool schema + executors
├── subagent.py   # isolated research/review agents
├── todo.py       # task tree
├── memory.py     # long-term memory
├── undo.py       # snapshots & rollback
├── mcp.py        # MCP protocol
├── session.py    # persistence
├── i18n.py       # en/zh strings
└── ui.py         # Rich terminal UI
```

## Design principles

1. **Pure Python, minimal deps** — starts in under a second
2. **Terminal-native UI** — Rich output, prompt_toolkit input
3. **Local-first** — no telemetry; offline capable
4. **Safety by default** — sandbox on until you opt out
5. **Extensible** — JSON-schema tools, MCP servers
