---
title: Quick Start
layout: docs
permalink: /guide/quick-start/
eyebrow: Guide
description: Install and run wow-agent in under a minute with uv.
---

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

## Install & run

```bash
# Ubuntu / Debian / WSL
cd wow-agent
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run wow
```

Windows (PowerShell, experimental):

```powershell
cd wow-agent
irm https://astral.sh/uv/install.ps1 | iex
$env:Path += ";$env:USERPROFILE\.local\bin"
uv sync; uv run wow
```

First launch walks you through provider + API key setup; config is saved to `~/.wow-agent.env` (mode 600).

## First commands

```text
$ wow
Enter auto mode? y/N
> Help me understand this project structure
```

- `!<cmd>` — run shell directly without the model (e.g. `!git status`)
- `/` — fuzzy command completion, `/help` lists everything

## Essential commands

| Command | Purpose |
|---|---|
| `/model` | switch provider/model wizard |
| `/status` | context · task progress · undoable changes |
| `/compact` | compress history manually |
| `/mem save/use/rm` | long-term memory |
| `/resume` | restore previous session |
| `/undo` | revert last change |
| `/review [path]` | read-only review: 🔴 high / 🟡 suggestion / 🟢 polish |
| `/language en\|zh` | UI language |
| `/safe` | toggle safe mode |

## Next steps

- Read [Why wow-agent](/why/)
- Explore the [Architecture](/architecture/)
