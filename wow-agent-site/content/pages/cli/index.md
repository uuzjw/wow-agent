---
title: CLI Reference
layout: docs
permalink: /cli/
eyebrow: Reference
description: The complete wow-agent command reference — every slash command, flag, shell escape and shortcut, with syntax, examples and expected output.
---

This is the exhaustive reference for everything you can type into wow-agent. For task-oriented learning, see the [Cookbook](/guide/cookbook/) instead.

## Launch-time options

```bash
uv run wow [options]
```

| Option | Effect |
|---|---|
| *(none)* | interactive session, confirmations on |
| `--auto` | auto mode: plan approved automatically (dangerous/egress still confirmed) |
| `--model <id>` | start with a specific model, e.g. `--model deepseek` or `--model ollama:llama3` |
| `--language en\|zh` | override UI language for this session |
| `--safe 0` | disable sandbox for this session (not recommended) |

---

## Slash commands

### `/help`

List every available command with a one-line summary. Aliases: `/h`, `?`.

### `/model`

The model control center.

```text
/model              interactive picker: provider → model
/model deepseek     quick switch by provider id
/model ollama:qwen2.5-coder:7b   provider:model syntax
/model --list       show models for current provider
/model --fetch      refresh list from provider API
/model --info       current model, context size, capabilities
```

Switching models mid-task is safe — conversation context is preserved.

### `/status`

The dashboard. Shows, at a glance:

```text
Session ─────────────────────────────
 Context    38,412 / 128,000 (30%)
 Task       fix-auth (EXECUTING, 3/5 subtasks)
 Undoable   4 snapshots
 Safety     sandbox ON · egress guard ON
 Model      deepseek-coder (128k ctx)
```

### `/compact [hint]`

Compress conversation history to reclaim context.

```text
/compact                    # automatic summarization
/compact keep the auth refactor details
/compact --aggressive       # maximum compression
```

Auto-compact also triggers at `WOW_AUTO_COMPACT` tokens. Hints steer what the summary preserves.

### `/undo`

Time travel for your working tree.

```text
/undo                # revert last change
/undo 3              # revert last 3
/undo --list         # history with snapshot ids
/undo --to=snap_4f2a # restore to a specific point
/undo --all          # revert everything this session
/undo --dry-run      # preview without touching files
```

Snapshots persist across restarts (see [Rollback](/safety/rollback/)).

### `/review [path] [--level=…]`

Read-only code review by a review sub-agent. Never modifies files.

```text
/review                          # whole project, medium level
/review src/auth/                # scoped
/review --changed                # only uncommitted changes
/review --level=high             # 🔴 security/correctness only
/review --level=low --format=markdown --output=review.md
```

Levels: `high` 🔴 security & correctness · `medium` 🟡 best practices (default) · `low` 🟢 polish & performance.

### `/mem`

Long-term memory across sessions.

```text
/mem save "project:auth" "JWT lives in src/auth/, refresh tokens in Redis"
/mem use "project:auth"     # load into current context
/mem list                   # everything, newest first
/mem rm "project:old"       # delete
```

Keys are namespaced by convention: `project:*`, `team:*`, `research:*`.

### `/safe`

```text
/safe              # toggle master safety switch
/safe status       # per-layer status
/safe logs         # recent events: blocks, confirms, rollbacks
/safe test         # self-test all four layers
```

### `/resume`

```text
/resume            # pick a previous session interactively
/resume --latest   # most recent, no menu
```

### `/snapshot create <label>`

Named checkpoint you can `/undo --to` later — do this before risky work.

### `/config [get|set|reset]`

```text
/config                     # dump effective config
/config get WOW_MAX_ITER
/config set WOW_MAX_ITER 60 # session-only override
/config reset               # back to defaults
```

### `/language [en|zh]`

Switch UI language immediately. Without argument: interactive menu.

### `/clear` and `/exit`

`/clear` wipes conversation (files untouched, asks to confirm). `/exit` saves session and quits. Aliases: `/q`, Ctrl+D.

---

## Shell escape `!`

Anything starting with `!` runs in your shell **without involving the model**:

```text
!git status
!pytest -x -q
!docker compose logs -f api
```

- Output streams into the session (truncated for context safety)
- Exit codes are shown; the agent can see them if you ask it to look
- Shell commands still pass the **safety system** (sandbox/egress/dangerous guards apply)

## Keyboard shortcuts

| Keys | Action |
|---|---|
| `Tab` | fuzzy-complete slash commands |
| `↑ / ↓` | prompt history |
| `Ctrl+C` | cancel current agent operation |
| `Ctrl+D` | exit |
| `Ctrl+L` | redraw screen |
| `Esc` | dismiss menu / suggestion |

## Exit codes (scripting)

| Code | Meaning |
|---|---|
| `0` | clean exit |
| `1` | provider/config error |
| `2` | safety guard blocked a required operation |
| `130` | interrupted by user (Ctrl+C) |
