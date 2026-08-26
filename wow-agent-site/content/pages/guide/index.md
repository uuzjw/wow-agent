---
title: Start Here
layout: docs
permalink: /guide/
eyebrow: User Guide
description: The friendly starting point for wow-agent users — what it is, a five-minute setup, and where to go next.
---

Welcome! This guide is written for people who just want to **get things done** with wow-agent — no prior agent experience needed.

## What is wow-agent, in one paragraph?

It is a coding partner that lives in your terminal. You describe a goal ("fix this bug", "add this feature", "why is this failing?"), and it **plans** the work, **executes** it with real tools (reading files, editing code, running tests), **verifies** the result, and **rolls back automatically** if verification fails. You can bring any AI model — cloud or local — and your code never leaves your machine unless you send it to a cloud provider yourself.

## The 5-minute quick path

```bash
# 1. Get it (Linux / macOS / WSL)
git clone https://github.com/uuzjw/wow-agent.git && cd wow-agent
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Launch — the wizard sets up your model
uv run wow
```

> Detailed instructions for every platform (including offline setups): [Installation](/guide/installation/).

## Two minutes on the safety model

An agent that runs commands must be constrained. wow-agent ships with four protective layers, all ON by default:

1. **Network sandbox** — the agent's shell cannot reach the internet
2. **Egress guard** — `git push`, `scp`, `curl POST` are blocked or confirmed
3. **Dangerous-command guard** — `rm -rf /` class commands require typing `YES`
4. **Rollback** — every file write is snapshotted; `/undo` reverts anything

You can read the full story in [Safety](/safety/). For now, know this: **a failed task cannot wreck your repo** — it rolls itself back.

## Your first real task

Read [Your First Task](/guide/first-task/) — a guided walkthrough showing every screen: the plan, the execution, the verification, and what to do when something goes wrong.

## After that

| I want to… | Go to |
|---|---|
| Copy-paste prompts that work | [Everyday Cookbook](/guide/cookbook/) |
| Master every command | [Commands](/guide/commands/) |
| Understand models & costs | [Model Ecosystem](/guide/model-eco/) |
| Know how it works inside | [Architecture](/architecture/) |
| Answers to common worries | [FAQ](/guide/faq/) |

## How the agent thinks (30-second version)

```text
you give a goal
  → PLANNING   it reads relevant code, proposes a task tree
  → EXECUTING  it works step by step, snapshotting every write
  → VERIFYING  it runs your tests to prove the result
  → DONE       or FAILED → automatic full rollback
```

That loop is the whole product. Everything else is detail.
