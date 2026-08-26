---
title: State Machine
layout: docs
permalink: /architecture/state-machine/
eyebrow: Architecture
description: How planning, executing, verifying, done and failed states drive every task.
---

```text
planning ──▶ executing ──▶ verifying ──▶ done
                │             │
                ▼             ▼
              failed ◀────────┘   → auto rollback → retry
```

## Transitions

- **planning → executing** — plan approved (manual or auto mode)
- **executing → verifying** — all subtasks complete
- **verifying → done** — tests/lint/types pass
- **verifying → failed** — checks fail; snapshots restored
- **any → failed** — critical error or max iterations

## What each state does

| State | Key actions |
|---|---|
| planning | query code index, build task tree, present plan |
| executing | pick ready subtasks, snapshot before writes, track progress |
| verifying | run test suite + linters + custom verifiers |
| done | summary, cleanup, memory updates |
| failed | reverse-order rollback of all task snapshots |

## Tuning

```bash
WOW_MAX_ITER=40          # iterations per task
WOW_ROLLBACK_ON_FAIL=1   # auto rollback on failure
```
