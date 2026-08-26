---
title: Comparison
layout: docs
permalink: /comparison/
eyebrow: Product
description: An honest, criteria-by-criteria comparison of wow-agent with browser chatbots, IDE copilots and terminal agents.
---

Four product categories solve "AI writes code" differently. This page maps the landscape honestly — including where wow-agent is *not* the best pick.

## The landscape

| Category | Examples | Core loop |
|---|---|---|
| Browser chatbot | ChatGPT, Claude.ai | paste code → chat → copy back |
| IDE copilot | Copilot, Cursor Tab | inline autocomplete as you type |
| IDE agent | Cursor Agent, Windsurf | multi-file edits inside an editor |
| **Terminal agent** | **wow-agent**, Claude Code, Aider | **goal → plan → tools → verified result** |

## Criteria matrix

| Criteria | Browser chat | IDE copilot | IDE agent | wow-agent |
|---|---|---|---|---|
| Works in your real repo | partial | ✔ | ✔ | ✔ |
| Multi-file task execution | ✗ | ✗ | ✔ | ✔ |
| Runs tests & verifies | ✗ | ✗ | partial | ✔ state machine |
| Model freedom (BYO key/vendor) | ✗ | ✗ | partial | ✔ 16+ + local |
| Runs fully offline | ✗ | ✗ | ✗ | ✔ Ollama/LM Studio |
| Network-isolated execution | ✗ | ✗ | ✗ | ✔ `unshare -n` |
| Egress guard (push/SCP block) | ✗ | ✗ | ✗ | ✔ |
| One-click rollback of agent edits | ✗ | ✗ | partial | ✔ snapshots + auto-rollback |
| ARM64 / edge devices | ✗ | ✗ | ✗ | ✔ Jetson-tested |
| Zero subscription (BYO keys) | ✗ | ✗ | ✗ | ✔ MIT, free |
| IDE integrations (hover, completions) | — | ✔✔ | ✔ | ✗ terminal only |
| GUI / visual diffs | ✔ | ✔ | ✔ | terminal diffs |

## Where wow-agent wins

1. **Trust architecture.** Sandbox + egress guard + confirmations + rollback is a defense-in-depth stack no IDE agent ships by default.
2. **Sovereignty.** Any provider, any key, or fully local — no vendor lock, no subscription, data stays home.
3. **Environments.** Pure terminal + ARM64 native means servers, containers, CI, Jetson boards — no IDE required.

## Where others win

1. **Inline completion.** If you want keystroke-level autocomplete in an editor, a copilot beats any agent — different tool layer.
2. **Visual UX.** Rich GUIs, image diffs, design previews — terminal output is powerful but not graphical.
3. **Ecosystem maturity.** Established products have larger plugin markets and support teams.

## Decision guide

| You are… | Best fit |
|---|---|
| Working in servers/SSH/containers daily | **wow-agent** |
| Privacy/compliance-sensitive, want local models | **wow-agent** |
| Automating multi-file tasks with verification | **wow-agent** |
| On an edge device / ARM64 SBC | **wow-agent** |
| Want autocomplete while typing | IDE copilot |
| Want a graphical agent inside VS Code | IDE agent |

## Combining tools

They're not mutually exclusive. A common setup: copilot for inline completion, wow-agent for **task-level work** — "implement this feature, prove it works, clean up after yourself."
