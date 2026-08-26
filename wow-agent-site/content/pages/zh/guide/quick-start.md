---
title: 快速开始
layout: docs
permalink: /zh/guide/quick-start/
eyebrow: 指南
description: 用 uv 在一分钟内安装并运行 wow-agent。
---

## 前置要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 包管理器

## 安装与运行

```bash
# Ubuntu / Debian / WSL
cd wow-agent
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run wow
```

Windows（PowerShell，实验性）：

```powershell
cd wow-agent
irm https://astral.sh/uv/install.ps1 | iex
$env:Path += ";$env:USERPROFILE\.local\bin"
uv sync; uv run wow
```

首次启动会引导配置服务商和 API Key，写入 `~/.wow-agent.env`（权限 600）。

## 首个命令

```text
$ wow
Enter auto mode? y/N
> 帮我看看这个项目的结构
```

- `!<命令>` — 不经模型直接跑 shell（如 `!git status`）
- `/` — 模糊补全命令，`/help` 查看全部

## 常用命令

| 命令 | 说明 |
|---|---|
| `/model` | 切换服务商/模型向导 |
| `/status` | 上下文 · 任务进度 · 可撤销改动 |
| `/compact` | 手动压缩历史 |
| `/mem save/use/rm` | 长期记忆管理 |
| `/resume` | 恢复历史会话 |
| `/undo` | 撤销最近修改 |
| `/review [路径]` | 只读审查：🔴高风险 / 🟡建议 / 🟢优化 |
| `/language en\|zh` | 界面语言 |
| `/safe` | 开/关安全模式 |

## 下一步

- 阅读[为什么选择](/zh/why/)
- 了解[架构设计](/zh/architecture/)
