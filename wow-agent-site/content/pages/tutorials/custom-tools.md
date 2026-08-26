---
title: Custom Tools
layout: docs
permalink: /tutorials/custom-tools/
eyebrow: Developer Tutorial
description: Teach wow-agent a new ability in ~30 lines — full walkthrough with schema, executor, safety level and testing.
---

In this tutorial you will add a `deploy` tool that lets the agent deploy a project to staging. Time: ~15 minutes.

## How tools work

A tool = **JSON Schema** (what the model sees) + **executor** (what actually runs) + **safety level** (what the guard requires). When the model decides to use a tool, wow-agent validates parameters against the schema, runs safety checks, snapshots if needed, then calls your executor.

## Step 1 — Declare the schema

Open `wow_agent/tools.py` and add to `TOOLS_SCHEMA`:

```python
"deploy": {
    "description": (
        "Deploy the current project to a target environment. "
        "Use only when the user explicitly asks to deploy."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "environment": {
                "type": "string",
                "enum": ["staging", "production"],
                "description": "Target environment",
            },
            "version": {
                "type": "string",
                "description": "Git ref or version tag; defaults to HEAD",
            },
        },
        "required": ["environment"],
    },
    "safety": "modify",       # safe | modify | destructive
    "confirmation": True,      # always ask the user first
}
```

Schema tips:

- `description` is prompt engineering — say **when** to use the tool
- `enum` prevents the model from inventing environments
- `confirmation: True` forces an interactive approve, even in auto mode

## Step 2 — Write the executor

```python
async def execute_deploy(params: dict, context) -> dict:
    import subprocess

    env = params["environment"]
    ref = params.get("version", "HEAD")

    result = subprocess.run(
        ["scripts/deploy.sh", env, ref],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        return {"success": False, "error": result.stderr[-2000:]}

    return {
        "success": True,
        "output": result.stdout[-2000:],
        "url": f"https://{env}.example.com",
    }

TOOL_EXECUTORS["deploy"] = execute_deploy
```

Executor contract:

- Receive validated `params` + execution `context`
- Return a dict with `success` — errors go back to the model so it can retry or explain
- Keep output bounded (`[-2000:]`) — huge outputs burn context

## Step 3 — Try it

```text
You > deploy current HEAD to staging

┌ PLANNING
│ 1. confirm deploy (requires approval)
│ 2. run deploy tool → staging @ HEAD
Approve? [Y/n] y

⚠ Deploy to staging — confirm? [y/N] y
✔ https://staging.example.com is live
```

Notice the **double confirmation**: once for the plan, once because `confirmation: True`.

## Step 4 — Test without an LLM

```python
# tests/test_tool_deploy.py
import asyncio
from wow_agent.tools import TOOL_EXECUTORS

def test_deploy_rejects_bad_env(monkeypatch):
    async def fake_run(*a, **k):
        class R: returncode = 1; stderr = "bad env"; stdout = ""
        return R()
    monkeypatch.setattr("subprocess.run", fake_run)
    result = asyncio.run(TOOL_EXECUTORS["deploy"]({"environment": "staging"}, None))
    assert result["success"] is False
```

Run offline:

```bash
uv run python tests_smoke.py
```

## Checklist

- [ ] Schema has helpful `description` + `enum` where possible
- [ ] Safety level matches reality (does it change state?)
- [ ] Output truncated to something context-friendly
- [ ] Offline unit test added
- [ ] Works with sandbox ON (no network needed, or documented)
