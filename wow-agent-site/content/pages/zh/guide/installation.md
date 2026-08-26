---
title: 安装
layout: docs
permalink: /zh/guide/installation/
eyebrow: 用户指南
description: wow-agent 全平台安装指南 —— Linux、macOS、WSL、Windows，以及离线与气隙环境部署。
---

本页覆盖所有受支持的安装方式，从 60 秒极速安装到完全离线环境。

## 环境要求

| 要求 | 最低版本 | 说明 |
|---|---|---|
| Python | 3.10+ | 推荐 3.11+ |
| [uv](https://docs.astral.sh/uv/) | 最新版 | 秒级安装的包管理器 |
| 磁盘 | ~200 MB | 含虚拟环境 |
| 内存 | 512 MB | Agent 本体；模型另计 |
| 网络 | 可选 | 本地模型可完全离线 |

## 一行命令安装（推荐）

Linux / macOS / WSL：

```bash
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run wow
```

Windows（PowerShell，实验性）：

```powershell
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent
irm https://astral.sh/uv/install.ps1 | iex
$env:Path += ";$env:USERPROFILE\.local\bin"
uv sync; uv run wow
```

## 首次启动会发生什么

1. 欢迎界面引导你**选择模型服务商**（DeepSeek、Qwen、OpenAI、Ollama…）
2. 粘贴 **API Key**（本地服务商不需要）
3. 配置写入 `~/.wow-agent.env`，权限 `600` —— 仅你的用户可读
4. 进入交互提示符，随时可以输入任务

```text
$ uv run wow

  Welcome to wow-agent!

  ? Select model provider › DeepSeek
  ? API Key › sk-****
  ? Model › deepseek-coder

  ✔ Config saved to ~/.wow-agent.env (600)

  You > _
```

## 不用 git 的安装方式

只要代码不要历史：

```bash
curl -L https://github.com/uuzjw/wow-agent/archive/refs/heads/main.tar.gz | tar xz
cd wow-agent-main && uv sync && uv run wow
```

## 离线 / 气隙环境安装

配合本地模型可完全离线工作：

```bash
# 1. 在有网的机器上
git clone https://github.com/uuzjw/wow-agent.git
cd wow-agent && uv sync

# 2. 整个文件夹拷贝到目标机器（U盘 / scp）
# 3. 目标机器上
uv run wow          # 选择 Ollama 或 LM Studio 作为服务商
```

模型本身离线化：

```bash
curl -fsSL https://ollama.ai/install.sh | sh   # 一次性，需网络
ollama pull deepseek-coder:6.7b                # 模型权重
ollama serve                                   # 本地端点 :11434
```

## 升级

```bash
cd wow-agent
git pull
uv sync
```

你的 `~/.wow-agent.env`、记忆和快照在升级后全部保留。

## 卸载

```bash
rm -rf wow-agent/           # 程序
rm ~/.wow-agent.env         # 配置
rm -rf ~/.wow-agent/        # 记忆 + 快照（可选）
```

## 故障排查

| 现象 | 解决 |
|---|---|
| `command not found: uv` | 重开终端或 `source ~/.bashrc`；或在项目目录 `uv run wow` |
| `Python 3.10 required` | uv 会自动管理 Python；执行 `uv python install 3.11` |
| `~/.wow-agent.env` 权限拒绝 | 文件本就是 600 权限；用你自己的用户运行，不要 root |
| 公司代理环境 | `uv sync` 前 `export HTTPS_PROXY=http://proxy:port` |
| Windows 装完找不到 uv | 重启 PowerShell 刷新 PATH |

## 下一步

- [第一个任务](/zh/guide/first-task/) —— 手把手实战演练
- [日常食谱](/zh/guide/cookbook/) —— 常见任务的现成配方
