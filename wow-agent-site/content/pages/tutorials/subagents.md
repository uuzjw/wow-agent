---
title: Sub-agents
layout: docs
permalink: /tutorials/subagents/
eyebrow: Developer Tutorial
description: How wow-agent's isolated sub-agents work, when the agent spawns them, and how to drive them effectively from prompts and code.
---

Sub-agents solve one problem: **research pollutes context**. A sub-agent gets a fresh context window, read-only tools, and returns only its conclusions.

## The model

```text
Main agent (full context, all tools)
   │ spawn(query, scope)
   ▼
Sub-agent (fresh context, read-only: read/grep/symbols/index)
   │ explores freely — none of it enters main context
   ▼
Structured result: { summary, key_files[], findings[], recommendations[] }
```

## When the agent spawns one

- You say **research/调研/investigate** in a prompt
- A plan step is pure information gathering
- `/review` is invoked (review sub-agent, read-only)

You'll see it in the transcript:

```text
▸ Spawning research agent (fresh context)
  … 14 file reads, 6 symbol queries (hidden from main context)
◀ Research complete — summary: 3 key files, 2 recommendations
```

## Driving sub-agents well

```text
# Good: bounded question, expected output shape
> Research: how does cache invalidation work after a write?
  List the exact functions involved and where they're called.

# Good: comparative research
> Research: compare auth middleware in src/auth/ vs the pattern
  used in examples/. Report differences as a table.

# Weak: open-ended
> Research the codebase
```

## What sub-agents cannot do

- Write, edit, delete (read-only tool set)
- Run shell commands
- See your conversation history — **you must state all context** in the query

## Configuration

```bash
WOW_MAX_SUBAGENTS=3      # concurrency cap
WOW_SUBAGENT_TIMEOUT=120 # seconds per spawn
WOW_SUBAGENT_MODEL=auto  # same model | fast model for research
```

## Extending (code level)

`wow_agent/subagent.py` exposes the spawner:

```python
result = await subagent_manager.spawn(
    type="research",            # research | review
    query="where are feature flags read?",
    scope=Path("src/"),         # limit exploration
    constraints=["ignore tests/"],
)
result.summary        # 2–3 sentence answer
result.key_files      # [FileRef(path, line)]
result.recommendations
```

Results are dataclasses — safe to feed into planning prompts.

## Design notes

- Fresh context per spawn: no cross-contamination between research tasks
- Token accounting: sub-agent spend is tracked separately and shown in `/status`
- Failure is cheap: a timed-out sub-agent returns partial findings, never blocks the main task
