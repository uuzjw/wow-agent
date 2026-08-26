---
title: Contributing
layout: docs
permalink: /tutorials/contributing/
eyebrow: Developer Tutorial
description: Set up a dev environment, navigate the codebase, run the test suite and ship your first wow-agent pull request.
---

## Dev setup (2 minutes)

```bash
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent
uv sync
uv run wow          # sanity check
```

## Where things live

```
wow_agent/
├── agent.py      # core loop + state machine (planning→executing→verifying)
├── cli.py        # entry point, slash commands, REPL
├── config.py     # PROVIDERS + env handling
├── indexer.py    # AST code index (symbols/references)
├── tools.py      # TOOLS_SCHEMA + executors + safety checks
├── subagent.py   # isolated research/review agents
├── todo.py       # task tree
├── memory.py     # long-term /mem store
├── undo.py       # snapshots & rollback
├── mcp.py        # MCP client
├── session.py    # session persistence
├── i18n.py       # EN/ZH strings
└── ui.py         # Rich rendering
```

**Rule of thumb**: new ability → `tools.py`; new slash command → `cli.py`; new model vendor → `config.py`; anything planning-related → `agent.py`.

## Tests (all offline, no API keys)

```bash
uv run python tests_smoke.py   # fast: imports, schemas, unit logic
uv run python tests_e2e.py     # fake-LLM end-to-end task runs
```

Both must pass before any PR. They run in seconds and never touch the network.

## Writing tests

- Unit-test tool executors with monkeypatched I/O (see `tests/test_tool_deploy.py` pattern in [Custom Tools](/tutorials/custom-tools/))
- E2E tests use the **fake LLM** — script tool calls, assert state-machine transitions
- Safety behaviors (egress patterns, dangerous commands) deserve a test each

## PR workflow

```bash
git checkout -b feat/my-feature
# ...code + tests...
uv run python tests_smoke.py && uv run python tests_e2e.py
git commit -m "feat(tools): add deploy tool with confirmation"
git push -u origin feat/my-feature
```

Conventions:

- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Scope in parens when obvious: `feat(providers): …`
- One logical change per PR; keep diffs reviewable
- Update docs (this site!) for user-facing changes — content lives in `wow-agent-site/content/`

## What we look for in review

1. Safety: does new code respect sandbox/egress/confirmation layers?
2. Offline: no mandatory network calls; tests stay offline
3. Context discipline: bounded outputs, no token bombs
4. i18n: user-facing strings go through `i18n.py` (EN + ZH)

## Issues

Good first issues are labeled `good first issue`. For bigger ideas, open a discussion first with the problem (not the solution) — designs get refined in the open.

## Docs contributions

This documentation site is static files: edit markdown in `wow-agent-site/content/pages/`, then:

```bash
cd wow-agent-site && bun run build   # verify locally
```

Typo fixes welcome — no issue needed.
