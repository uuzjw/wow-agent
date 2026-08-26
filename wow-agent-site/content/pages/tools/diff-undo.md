---
title: Diff & Undo
layout: docs
permalink: /tools/diff-undo/
eyebrow: Tools
description: Colored diffs, single-step /undo, task-level rollback and cross-restart snapshots.
---

## Diffs

Every modification renders a unified colored diff before it applies:

```diff
- def process_payment(amount):
+ def process_payment(amount: float) -> PaymentResult:
+     if amount <= 0:
+         raise ValueError("Amount must be positive")
```

## Undo

```bash
/undo                # revert last change
/undo 3              # last three
/undo --list         # history with timestamps
/undo --to=snap_abc  # restore to a snapshot
/undo --dry-run      # preview only
```

## Automatic rollback

When verification fails, **every snapshot from the task is restored in reverse order** and files created during the task are deleted.

```text
Task "Add auth"
├── ✔ model created        (snap_1)
├── ✔ endpoint added       (snap_2)
├── ✘ tests failed
└── ↩ rollback → repo back to pre-task state
```

## Storage

Snapshots live in `~/.wow-agent/snapshots/` (diff + metadata), survive restarts, capped by `WOW_MAX_SNAPSHOTS` (default 1000) with a 30-day TTL.
