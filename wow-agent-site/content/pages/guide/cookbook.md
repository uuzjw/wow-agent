---
title: Everyday Cookbook
layout: docs
permalink: /guide/cookbook/
eyebrow: User Guide
description: Copy-paste recipes for the jobs people actually give wow-agent — exploring, fixing, building, testing, reviewing and refactoring.
---

Ten proven recipes. Each one is a prompt you can adapt directly — no ceremony, just what works.

## 1. Understand an unfamiliar codebase

```text
> Give me a tour of this repo: entry points, main modules,
  and how data flows between them. Keep it under 30 lines.
```

*Why it works: asks for a bounded summary, so the answer stays readable.*

## 2. Find where something happens

```text
> Where do we validate user permissions? Show me every code path
  that can reject a request, with file:line references.
```

## 3. Fix a bug (with reproduction)

```text
> Bug: uploading a 0-byte file creates a broken record.
  1. Write a failing test that reproduces it
  2. Fix the bug
  3. Show me the diff and run the full test suite
```

*The agent will plan → test-first → fix → verify. This ordering catches regressions for free.*

## 4. Add a feature end-to-end

```text
> Add a DELETE /api/v1/items/{id} endpoint:
  - 404 when missing, 204 on success
  - permission check via existing require_role decorator
  - repository + service + handler layers, matching existing style
  - tests for both outcomes
```

## 5. Write tests for legacy code

```text
> tests/ has nothing for src/billing/. Write unit tests for
  InvoiceService covering: happy path, proration edge cases,
  and the currency rounding bug mentioned in TODO comments.
  Use mocks for the DB layer.
```

## 6. Refactor safely

```text
> src/legacy/parser.py is 900 lines. Split it into modules
  under src/parsing/ WITHOUT changing public behavior.
  Run the test suite before and after; do not touch the API.
```

*"Without changing public behavior" is the magic phrase — it sets the verification bar.*

## 7. Review code before you push

```text
/review --changed --level=high
```

Security & correctness only, on your uncommitted changes. Full tri-level review: `/review src/module/`.

## 8. Explain a cryptic error

```text
> pytest just failed with "RuntimeError: coroutine was never awaited"
  in test_orders.py. Explain the cause and fix all occurrences.
```

## 9. Dependency & upgrade work

```text
> Upgrade requirements.txt to SQLAlchemy 2.x.
  Migrate query patterns that changed, run tests,
  and list every behavioral difference you noticed.
```

## 10. Generate project documentation

```text
> Write docs/API.md: every public endpoint, request/response
  examples from the test fixtures, and error codes.
  Match the tone of README.md.
```

## Universal prompt patterns

| Pattern | Example |
|---|---|
| **Constraints** | "don't change public APIs", "no new dependencies" |
| **Definition of done** | "tests pass, lint clean" |
| **Style anchors** | "match the style of src/services/user.py" |
| **Step ordering** | "test first, then fix" |
| **Scope fences** | "only touch src/auth/, nothing else" |

## Power combos

```text
# Morning triage
/review --changed --level=high
> Run the full test suite and summarize failures

# Before opening a PR
> Write a conventional-commit message for the current staged diff
> Summarize this diff for a PR description, list risks
```
