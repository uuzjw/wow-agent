---
title: FAQ
layout: docs
permalink: /guide/faq/
eyebrow: User Guide
description: Straight answers to the questions new wow-agent users ask most — models, privacy, safety, cost and daily workflow.
---

## Do I need an API key?

Not necessarily. Choose **Ollama** or **LM Studio** during setup and everything runs on your machine with zero keys. Cloud providers need their own key.

## Where does my code go?

Nowhere, unless you choose a cloud model. With local models, inference happens on your machine and nothing leaves it. With cloud models, only the context you approve is sent to that provider. The agent itself has **no telemetry**.

## Is it safe to let it run commands?

By default, three layers protect you:

1. **Network sandbox** — the agent's shell has no internet access
2. **Egress guard** — `git push`, `scp`, `curl POST`, `npm publish` are blocked or confirmed
3. **Dangerous-command guard** — `rm -rf /`, `dd`, fork bombs require typing `YES`

Plus every file write is snapshotted: `/undo` reverts anything.

## What does it cost?

The agent is free (MIT). Model costs depend on provider:

- **Free**: Ollama / LM Studio (your hardware), OpenCode Zen free tier
- **Cheap**: DeepSeek and Qwen free/low tiers cover most daily coding
- Pay only for what you use — no subscription, no per-seat fees

## Which model should I start with?

| Your case | Start with |
|---|---|
| Just trying out | OpenCode Zen free tier |
| Privacy first | Ollama `deepseek-coder:6.7b` |
| Best quality | DeepSeek `deepseek-coder` or GPT-4o |
| Weak machine | Qwen smaller tiers via API |

## How is this different from ChatGPT/Claude in a browser?

Those chat about code; wow-agent **works in your repo**: reads files via a code index, edits them with diffs, runs your tests, verifies results, rolls back failures. It operates where the code lives.

## How is this different from IDE copilots?

Copilots autocomplete inside an editor. wow-agent is a **task agent**: you give a goal ("fix this bug"), it plans, edits multiple files, runs verification, and reports. Different tool for a different job layer.

## Can I use it at work?

Yes — MIT licensed. Safety defaults (sandbox + egress guard) make it suitable for proprietary code. For strict compliance, run fully offline with local models.

## Does it work on Windows / ARM?

- **Windows**: PowerShell, experimental
- **macOS**: native (Apple Silicon included)
- **Linux**: primary platform
- **ARM64**: first-class — tested on Jetson Orin NX

## The agent "failed" — did it break my repo?

Almost certainly not. Failed tasks trigger **automatic rollback**: every snapshot from the task is restored in reverse order. Check `/safe logs` for the record, and `/undo --list` anytime.

## Context is filling up — what do I do?

```text
/compact              # compress history now
/compact keep auth    # compress, preserve auth-related context
```

Auto-compact triggers at `WOW_AUTO_COMPACT` tokens by itself. For long-running knowledge, use `/mem save`.

## How do I report a bug or request a feature?

[GitHub Issues](https://github.com/uuzjw/wow-agent/issues) — PRs welcome, see [Contributing](/tutorials/contributing/).
