---
title: 模型生态
layout: docs
permalink: /zh/guide/model-eco/
eyebrow: 核心概念
description: 16+ 云端服务商与完全本地模型，统一接口接入。
---

## 云端服务商

DeepSeek · Qwen · Kimi · GLM · SiliconFlow · 豆包 · 混元 · MiniMax · OpenRouter · Groq · Mistral · Grok · OpenAI · Gemini · OpenCode Zen（免费档含 `x-preview-f-free`）

## 本地模型

| 服务商 | 启动 | 说明 |
|---|---|---|
| Ollama | `ollama serve` | 无需 Key，100% 离线 |
| LM Studio | GUI + 本地服务 | 任意 GGUF 模型 |

## 切换

```bash
/model                 # 交互向导
/model deepseek        # 快速切换
/model ollama:llama3   # 本地模型
```

## 选型建议

| 目标 | 推荐 |
|---|---|
| 编程质量最佳 | DeepSeek Coder、GPT-4o |
| 速度 | Groq (Llama3)、Gemini Flash |
| 免费 | DeepSeek / Qwen 免费档、OpenCode Zen |
| 隐私 | Ollama codellama / deepseek-coder |
| 长上下文 | Kimi (200k)、Gemini 1.5 Pro (1M) |

记得设置 `WOW_MODEL_CTX` 让上下文估算与模型匹配。
