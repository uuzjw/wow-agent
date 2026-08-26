---
title: File Operations
layout: docs
permalink: /tools/file-ops/
eyebrow: Tools
description: read, write, edit, delete, glob and list — with snapshots on every change.
---

## Read

```bash
> Read src/main.py            # whole file
> Read src/main.py:10-50      # line range
```

## Edit (precise replacement)

```bash
> Edit src/user.py
# find:    "def get_user(id):"
# replace: "def get_user(id: int) -> User:"
```

`old_string` must match exactly — include enough surrounding context to be unique. A colored diff is shown before applying.

## Write & delete

- `write` creates or overwrites; overwrites snapshot first
- `delete` always asks for confirmation

## Search

```bash
> Grep "TODO" --include="*.py"
> Glob "src/**/test_*.py"
> Symbols *Service            # from the code index, faster than grep
```

Every modifying operation creates a rollback snapshot automatically.
