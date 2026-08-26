---
title: Agent Brain
layout: docs
permalink: /guide/agent-brain/
eyebrow: Core Concept
description: Task planning, the planning→executing→verifying state machine and clean-context sub-agents.
---

## Task planning

High-level goals are decomposed automatically:

```
Goal: "Add JWT authentication"
├── research existing auth patterns
├── design token schema
├── implement model + middleware
├── add login/register endpoints
└── write tests, update docs
```

The plan is shown for approval unless auto mode is on.

## State machine

```text
planning → executing → verifying → done
                ↘            ↗
                 failed ←────┘   (auto rollback)
```

| State | What happens |
|---|---|
| planning | analyze repo via code index, build task tree |
| executing | call tools, snapshot before each write |
| verifying | run tests/lint/type-checks |
| failed | full-task rollback, error report |

## Sub-agents

- **Research** — clean context, read-only tools, returns a concise summary so the main context stays unpolluted
- **Review** — powers `/review` with three severity levels (🔴 high risk · 🟡 suggestion · 🟢 polish)

## Memory

Short-term history auto-compacts at `WOW_AUTO_COMPACT` tokens. Long-term knowledge persists across sessions:

```bash
/mem save "project:payment" "Stripe webhooks in payment/webhooks.py"
```
