---
title: Changelog
layout: docs
permalink: /changelog/
eyebrow: Product
description: Release history for wow-agent — what shipped in every version, newest first.
---

Format based on [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## v0.6.0 — current release

**The safety & scale release.**

### Added
- Four-layer safety system: `unshare -n` network sandbox, egress guard (`curl POST`/`scp`/`git push`/`npm publish`), dangerous-command double confirmation, snapshot rollback
- `/review` three-level code review (🔴 high / 🟡 medium / 🟢 low) via review sub-agent
- AST-based Python code index: symbols, references, definitions with incremental updates
- Long-term memory: `/mem save/use/rm/list/new`
- MCP client: run any Model Context Protocol server, tools auto-discovered
- Bilingual UI (EN/ZH) with `/language`
- ARM64 support, tested on Jetson Orin NX

### Changed
- State machine hardened: failed tasks auto-rollback every snapshot
- `/model --fetch` pulls live model lists from providers
- Session persistence improved: `/resume` across restarts

### Performance
- Agent cold start under one second
- Index incremental update ~50 ms per changed file

## v0.5.0

### Added
- Sub-agent system: fresh-context research agents with structured results
- Diff visualization for every file modification
- `/compact [hint]` guided history compression

### Fixed
- Snapshot integrity across sessions (`/undo --verify`)

## v0.4.0

### Added
- Provider presets: DeepSeek, Qwen, Kimi, GLM, SiliconFlow, OpenAI, Gemini, Ollama, LM Studio
- `/model --fetch` online model listing
- Shell escape `!command` with safety checks

## v0.3.0

### Added
- Task tree planning with user approval
- Snapshot-based `/undo` (single and multi-step)
- `/status` dashboard

## v0.2.0

### Added
- Tool-calling loop with JSON-schema validation
- File tools: read/write/edit/delete/list/glob/grep
- Shell tool with timeout control

## v0.1.0

- Initial public release: interactive terminal REPL, OpenAI-compatible chat, basic planning

---

Older detail lives in [GitHub Releases](https://github.com/uuzjw/wow-agent/releases).
