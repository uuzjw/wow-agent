---
title: Sub-Agents
layout: docs
permalink: /architecture/sub-agents/
eyebrow: Architecture
description: Isolated research and review agents that keep the main context clean.
---

## Why

Research burns context. Sub-agents run in a **clean context**, use read-only tools, and return a structured summary — the main agent only sees conclusions, not the noise.

## Types

| Type | Tools | Returns |
|---|---|---|
| Research | read · grep · symbols · index | summary + key files + recommendations |
| Review | read-only | 🔴 high risk / 🟡 suggestion / 🟢 polish issues |

## Example flow

```text
Main: "I need to understand the payment flow"
  └─▶ spawn research agent (fresh context)
        reads payment/*.py, greps "webhook", queries symbols
      ◀─ summary: "Stripe + idempotency keys; see service.py:45 …"
Main: continues planning with zero pollution
```

## Usage

```bash
/review src/payment/ --level=high
> Research: how is cache invalidation implemented?
```

Concurrency is capped (`WOW_MAX_SUBAGENTS=3`) and each spawn has its own timeout.
