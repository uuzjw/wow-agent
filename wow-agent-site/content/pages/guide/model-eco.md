---
title: Model Ecosystem
layout: docs
permalink: /guide/model-eco/
eyebrow: Core Concept
description: 16+ cloud providers plus fully local models behind one unified interface.
---

## Cloud providers

DeepSeek · Qwen · Kimi · GLM · SiliconFlow · Doubao · Hunyuan · MiniMax · OpenRouter · Groq · Mistral · Grok · OpenAI · Gemini · OpenCode Zen (free tier includes `x-preview-f-free`)

## Local models

| Provider | Setup | Notes |
|---|---|---|
| Ollama | `ollama serve` | no API key, 100% offline |
| LM Studio | GUI + local server | any GGUF model |

## Switching

```bash
/model                 # interactive wizard
/model deepseek        # quick switch
/model ollama:llama3   # local model
```

## Picking a model

| Goal | Recommendation |
|---|---|
| Best coding quality | DeepSeek Coder, GPT-4o |
| Speed | Groq (Llama3), Gemini Flash |
| Free | DeepSeek / Qwen free tiers, OpenCode Zen |
| Privacy | Ollama codellama / deepseek-coder |
| Long context | Kimi (200k), Gemini 1.5 Pro (1M) |

Set `WOW_MODEL_CTX` so context estimation matches your model.
