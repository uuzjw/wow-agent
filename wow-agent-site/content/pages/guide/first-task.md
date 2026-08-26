---
title: Your First Task
layout: docs
permalink: /guide/first-task/
eyebrow: User Guide
description: A step-by-step guided walkthrough of giving wow-agent its first real coding task, from prompt to verified result.
---

This walkthrough takes you through a complete real task: **"add input validation to a function and fix the bug you find"**. Every screen you will see is shown.

## 1. Start the agent

```bash
cd my-project
uv run wow
```

You are asked `Enter auto mode? y/N`:

- **N (default, recommended at first)** — the agent shows its plan and asks before writing anything
- **y** — it works without step-by-step confirms; dangerous commands and data-egress attempts *still* require approval

## 2. Describe the goal, not the steps

```text
You > The function parse_config in src/config.py crashes when the file
      has duplicate keys. Find out why and fix it properly.
```

Tips for a good first prompt:

- ✅ say **what is wrong** and **where** (even roughly)
- ✅ say what "fixed" means to you
- ❌ don't dictate exact line edits — planning is the agent's job

## 3. Watch the plan (PLANNING state)

The agent reads the relevant files via its code index, then shows a task tree:

```text
┌ PLANNING ───────────────────────────────────────────┐
│ 1. Read src/config.py and reproduce the crash       │
│ 2. Identify root cause (duplicate-key handling)     │
│ 3. Implement fix + add regression test              │
│ 4. Run test suite                                    │
│ Approve plan? [Y/n]                                  │
└──────────────────────────────────────────────────────┘
```

Press **Y** to approve. Want changes first? Type feedback like `n` then
`also log a warning when duplicates are merged`.

## 4. Execution (EXECUTING state)

The agent works through subtasks. Before **every** file write it takes a snapshot (this is what makes `/undo` possible):

```text
┌ EXECUTING 2/4 ──────────────────────────────────────┐
│ ▸ Reading src/config.py (48 lines)                  │
│ ✔ Root cause: dict overwrite in load(), line 31     │
│ ▸ Edit src/config.py                                │
│   @@ -28,7 +28,12 @@                                 │
│   -    data = json.load(f)                           │
│   +    data = json.load(f, object_pairs_hook=...)    │
│ snapshot snap_4f2a saved                             │
└──────────────────────────────────────────────────────┘
```

## 5. Verification (VERIFYING state)

When implementation is done, the agent **proves** it:

```text
┌ VERIFYING ──────────────────────────────────────────┐
│ ✔ pytest tests/test_config.py -q   12 passed        │
│ ✔ ruff check .                     clean            │
│ Task complete in 3m 41s                             │
└──────────────────────────────────────────────────────┘
```

## 6. If anything goes wrong

```text
You > /undo          # revert the last change
You > /undo --list   # see everything revertable
```

If verification fails, wow-agent **rolls the whole task back automatically** — your repo returns to the exact pre-task state, and you get an error report.

## 7. Wrap up

```text
You > /status        # context used, task progress
You > !git diff      # inspect changes with your own eyes
You > !git add -A && git commit -m "fix: duplicate-key crash in parse_config"
```

## What you just learned

| Concept | What it means |
|---|---|
| State machine | planning → executing → verifying → done/failed |
| Snapshots | every write is revertible via `/undo` |
| Verification | tests/lint must pass before "done" |
| Auto rollback | failed tasks restore your repo automatically |

## Where to go next

- [Everyday Cookbook](/guide/cookbook/) — 10+ ready-made recipes
- [Commands](/guide/commands/) — the full slash-command toolbox
