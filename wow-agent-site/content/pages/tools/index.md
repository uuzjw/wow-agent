---
title: Tools Overview
layout: docs
permalink: /tools/
eyebrow: Reference
description: File operations, search, diff/undo, shell and MCP — the agent's hands.
---

| Category | Tools | Safety |
|---|---|---|
| File | `read` `write` `edit` `delete` `list` `glob` | safe → destructive |
| Search | `grep` `symbols` `references` `definition` | safe |
| Code | `index` `diff` `patch` | safe / modify |
| System | `shell` `git` | guarded by safety layers |

## Execution pipeline

```text
validate params → safety check → snapshot → execute → verify → result
                                      │              │
                                      └── rollback ◀─┘ (on failure)
```

## Adding a custom tool

```python
TOOLS_SCHEMA["deploy"] = {
    "description": "Deploy to staging",
    "parameters": {...},
    "safety": "modify",
}
async def execute_deploy(params, ctx): ...
```

Deep dives: [File Operations](/tools/file-ops/) · [Diff & Undo](/tools/diff-undo/) · [MCP](/tools/mcp/)
