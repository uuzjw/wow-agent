---
title: Why wow-agent
layout: docs
permalink: /why/
eyebrow: Guide
description: Model freedom, local-first runtime, native ARM64 and safety by default — the reasons teams pick wow-agent.
---

## The old way is broken

- **Context loss** — copy/paste between editor and chat
- **No execution** — AI cannot run tests or verify changes
- **You are the bridge** — manual integration of every snippet
- **No guardrails** — suggestions applied directly, no undo

## The wow-agent way

| Principle | Implementation |
|---|---|
| Agent, not assistant | Executes real operations in your repo |
| Local-first | Zero telemetry; works fully offline with local models |
| Model agnostic | 16+ cloud providers + Ollama/LM Studio |
| Safety by default | Sandbox, egress guard, confirmations, rollback |
| Extensible | MCP protocol + custom tools + sub-agents |

## Comparison

| Difference | Traditional tools | wow-agent |
|---|---|---|
| Models | locked to one vendor | any OpenAI-compatible API |
| Runtime | IDE / cloud bound | pure terminal |
| Arch | x86 only | native ARM64 |
| Safety | direct execution | sandbox + rollback |

> One sentence: **model choice, environment control, safety decisions.**
