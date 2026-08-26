---
title: Rollback System
layout: docs
permalink: /safety/rollback/
eyebrow: Safety · Layer 4
description: Snapshot-based undo that survives restarts and restores whole failed tasks automatically.
---

## Manual

```bash
/undo                  # last change
/undo 3                # last three
/undo --list           # what can be reverted
/undo --to=snap_xxx    # point-in-time restore
/undo --all            # entire session
/undo --dry-run        # preview
```

## Automatic

Task failure during verification triggers a full rollback: snapshots restored in reverse order, task-created files deleted, directories cleaned.

## Snapshots

```json
{
  "id": "snap_a1b2c3d4",
  "operation": "edit",
  "target": "src/auth.py",
  "diff": "@@ -10,7 +10,12 @@ …"
}
```

- stored in `~/.wow-agent/snapshots/`
- cross-restart persistent
- `WOW_MAX_SNAPSHOTS=1000`, TTL 30 days
- `/undo --verify` checks integrity

## Tips

1. Label risky checkpoints: `/snapshot create "before-refactor"`
2. Dry-run first when unsure
3. Combine with git for milestone commits
