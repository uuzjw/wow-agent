---
title: Commands Reference
layout: docs
permalink: /guide/commands/
eyebrow: Guide
description: Every slash command, shell escape and keyboard shortcut in wow-agent.
---

## Core

| Command | Description |
|---|---|
| `/help` | list all commands |
| `/model [id]` | switch provider/model; `--list`, `--fetch`, `--info` |
| `/status` | context usage, task progress, undoable changes |
| `/compact [hint]` | compress conversation history |
| `/clear` | clear conversation |
| `/exit` | quit |

## Memory

```bash
/mem save "project:auth" "JWT lives in src/auth/"
/mem use "project:auth"
/mem list
/mem rm "project:old"
```

## Review & Safety

```bash
/review src/auth/ --level=high   # security-focused review
/safe status                     # sandbox + egress state
/safe logs                       # recent safety events
/undo                            # single-step revert
/undo 3                          # revert last three changes
/undo --to=snap_abc123           # restore a snapshot
```

## Shell escape

```bash
!git status          # runs immediately, no model involved
!pytest -x tests/    # output streams into the session
```

## Aliases

`/h` → help · `/m` → model · `/s` → status · `/u` → undo · `/r` → review
