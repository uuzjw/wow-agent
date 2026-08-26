---
title: Data Flow
layout: docs
permalink: /architecture/dataflow/
eyebrow: Architecture
description: Follow one user goal through wow-agent end-to-end — every hop, every guard, every snapshot, from prompt to verified result.
---

Trace a single request — *"fix the duplicate-key bug in src/config.py"* — through the machine.

## The full path

```text
You
 │ "fix the duplicate-key bug…"
 ▼
┌──────────────────────── CLI (cli.py) ────────────────┐
│ parse input → route: chat? command? shell escape?    │
└──────────────────────┬───────────────────────────────┘
                       ▼
┌───────────────── AGENT BRAIN (agent.py) ─────────────┐
│ 1. load memory (/mem) + session context              │
│ 2. query CODE INDEX for relevant symbols             │
│ 3. ask model for a PLAN → task tree (todo.py)        │
│ 4. state: PLANNING → show plan → approve?            │
└──────────────────────┬───────────────────────────────┘
                       ▼ plan approved
┌──────────────────── EXECUTING ───────────────────────┐
│ for each subtask:                                    │
│   model picks a TOOL + arguments                     │
│        │                                             │
│        ▼                                             │
│   ┌─ SAFETY GATE (tools.py) ──────────────┐          │
│   │ schema validation → egress patterns  │          │
│   │ → dangerous-command check → confirm? │          │
│   └──────────────┬────────────────────────┘          │
│                  ▼                                   │
│   snapshot (undo.py) → EXECUTE tool                  │
│                  ▼                                   │
│   result back to model (bounded output)              │
└──────────────────────┬───────────────────────────────┘
                       ▼ all subtasks done
┌──────────────────── VERIFYING ───────────────────────┐
│ run tests + lint via shell tool                      │
│   pass → DONE (summary, memory update)               │
│   fail → FAILED → auto-rollback all task snapshots   │
└──────────────────────────────────────────────────────┘
```

## Hop-by-hop details

### 1. Context assembly

Before any model call, the brain assembles: system prompt + i18n strings + conversation + memory entries + **code index hits** for keywords in your goal. Index hits mean the model reads `config.py`'s symbol outline, not the whole repo.

### 2. Planning call

The model returns a task tree (JSON). `todo.py` validates dependencies and stores it. Auto mode skips the approval gate — dangerous steps still confirm later.

### 3. Tool selection loop

Each iteration: model emits `{tool, params}` → schema-validated → safety-gated → snapshotted → executed. The result (truncated, e.g. last 2000 chars) returns as a tool message. Loop continues until the model signals completion or `WOW_MAX_ITER` hits.

### 4. The safety gate ordering

```text
validate params ──▶ egress patterns ──▶ dangerous patterns ──▶ confirmation
      │                    │                     │                  │
   400-ish            BLOCK/log             BLOCK/log          typed YES
```

Order matters: cheap checks first; confirmations last, only for what survives.

### 5. Snapshots

`undo.py` diffs the target file pre-write, stores `{meta, diff}` under `~/.wow-agent/snapshots/`, links it to the current task id. Task failure walks task-linked snapshots in reverse.

### 6. Verification

The shell tool runs your project's tests (auto-detected: pytest/npm test/go test…). Non-zero exit → verification failure → rollback + failure report with the exact command output that failed.

## What touches the network?

| Hop | Network? |
|---|---|
| model API calls | yes — to your chosen provider only |
| tool execution (sandboxed) | **no** — namespace-isolated |
| MCP servers | inherit sandbox |
| telemetry | none exists |

## Failure containment

Any layer can fail without corrupting state: model errors → retry/next iteration; tool errors → returned to model for self-correction; verification failure → rollback; crash → session + snapshots persist on disk.
