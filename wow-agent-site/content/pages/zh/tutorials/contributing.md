---
title: 参与贡献
layout: docs
permalink: /zh/tutorials/contributing/
eyebrow: 开发者教程
description: 搭建开发环境、读懂代码结构、跑通测试套件，提交你的第一个 wow-agent Pull Request。
---
## 开发环境（2 分钟）
```bash
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent
uv sync
uv run wow          # 冒烟检查
```
## 代码都在哪
```
wow_agent/
├── agent.py      # 核心循环 + 状态机（planning→executing→verifying）
├── cli.py        # 入口、斜杠命令、REPL
├── config.py     # PROVIDERS + 环境变量
├── indexer.py    # AST 代码索引（符号/引用）
├── tools.py      # TOOLS_SCHEMA + 执行器 + 安全检查
├── subagent.py   # 隔离的调研/审查代理
├── todo.py       # 任务树
├── memory.py     # 长期 /mem 存储
├── undo.py       # 快照与回滚
├── mcp.py        # MCP 客户端
├── session.py    # 会话持久化
├── i18n.py       # 中英文案
└── ui.py         # Rich 渲染
```
**经验法则**：新能力 → `tools.py`；新斜杠命令 → `cli.py`；新模型厂商 → `config.py`；规划相关 → `agent.py`。
## 测试（全部离线，无需 API Key）
```bash
uv run python tests_smoke.py   # 快：导入、Schema、单元逻辑
uv run python tests_e2e.py     # 假 LLM 端到端任务
```
任何 PR 前两者都必须绿。秒级运行，绝不碰网。
## 写测试
- 用 monkeypatch 打桩 I/O 来单测工具执行器（见[自定义工具](/zh/tutorials/custom-tools/)的 `tests/test_tool_deploy.py` 模式）
- E2E 测试用**假 LLM** —— 编排工具调用，断言状态机转换
- 安全行为（外传模式、高危命令）每个都值得单独一个测试
## PR 流程
```bash
git checkout -b feat/my-feature
# ...写代码 + 测试...
uv run python tests_smoke.py && uv run python tests_e2e.py
git commit -m "feat(tools): add deploy tool with confirmation"
git push -u origin feat/my-feature
```
约定：
- Conventional commits：`feat:`、`fix:`、`docs:`、`refactor:`、`test:`
- 范围明确时加括号：`feat(providers): …`
- 一个 PR 一个逻辑变更；保持 Diff 可审
- 用户可见的变更同步更新文档站（内容在 `wow-agent-site/content/`）
## Review 看什么
1. 安全：新代码是否尊重沙盒/外传/确认层？
2. 离线：无强制联网；测试保持离线
3. 上下文纪律：输出有界，不扔 Token 炸弹
4. 国际化：用户可见文案走 `i18n.py`（中英双语）
## Issue
`good first issue` 标签适合上手。大想法先开 Discussion 讲**问题**（不是方案）—— 设计在公开讨论中打磨。
## 文档贡献
本站是纯静态文件：编辑 `wow-agent-site/content/pages/` 下的 Markdown，然后：
```bash
cd wow-agent-site && bun run build   # 本地验证
```
改错别字不用开 Issue，直接 PR。
