---
title: Installation
layout: docs
permalink: /guide/installation/
eyebrow: User Guide
description: Complete installation guide for wow-agent on Linux, macOS, WSL and Windows — including offline and air-gapped setups.
---

This page covers every supported way to install wow-agent, from a 60-second setup to fully offline environments.

## Requirements

| Requirement | Minimum | Notes |
|---|---|---|
| Python | 3.10+ | 3.11+ recommended |
| [uv](https://docs.astral.sh/uv/) | latest | package manager, installs in seconds |
| Disk | ~200 MB | incl. virtual environment |
| RAM | 512 MB | agent itself; your model needs its own |
| Network | optional | fully offline possible with local models |

## One-line install (recommended)

Linux, macOS, WSL:

```bash
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run wow
```

Windows (PowerShell, experimental):

```powershell
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent
irm https://astral.sh/uv/install.ps1 | iex
$env:Path += ";$env:USERPROFILE\.local\bin"
uv sync; uv run wow
```

## What happens on first launch

1. A welcome screen appears and asks you to **pick a model provider** (DeepSeek, Qwen, OpenAI, Ollama, …)
2. You paste your **API key** (not needed for local providers)
3. wow-agent writes `~/.wow-agent.env` with permission `600` — only your user can read it
4. You land in the interactive prompt, ready to type a task

```text
$ uv run wow

  Welcome to wow-agent!

  ? Select model provider › DeepSeek
  ? API Key › sk-****
  ? Model › deepseek-coder

  ✔ Config saved to ~/.wow-agent.env (600)

  You > _
```

## Installing without git

Only want the code, no history?

```bash
curl -L https://github.com/uuzjw/wow-agent/archive/refs/heads/main.tar.gz | tar xz
cd wow-agent-main && uv sync && uv run wow
```

## Offline / air-gapped installation

wow-agent works fully offline with local models:

```bash
# 1. On a machine WITH internet
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent && uv sync

# 2. Copy the whole folder to the target machine (USB / scp)
# 3. On the target machine
uv run wow          # pick Ollama or LM Studio as provider
```

Run the model itself offline:

```bash
curl -fsSL https://ollama.ai/install.sh | sh   # once, with internet
ollama pull deepseek-coder:6.7b                # model weights
ollama serve                                   # local endpoint :11434
```

## Upgrading

```bash
cd wow-agent
git pull
uv sync
```

Your `~/.wow-agent.env`, memory and snapshots survive upgrades.

## Uninstall

```bash
rm -rf wow-agent/           # the app
rm ~/.wow-agent.env         # config
rm -rf ~/.wow-agent/        # memory + snapshots (optional)
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `command not found: uv` | re-open shell or `source ~/.bashrc`; or run `uv run wow` from the project folder |
| `Python 3.10 required` | uv usually manages Python itself; run `uv python install 3.11` |
| `permission denied` on `~/.wow-agent.env` | file is mode 600 by design; run as your own user, not root |
| behind a corporate proxy | `export HTTPS_PROXY=http://proxy:port` before `uv sync` |
| Windows: `uv` not found after install | restart PowerShell so PATH refreshes |

## Next steps

- [Your First Task](/guide/first-task/) — a guided walkthrough
- [Everyday Cookbook](/guide/cookbook/) — recipes for common jobs
