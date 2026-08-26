---
title: 添加模型服务商
layout: docs
permalink: /zh/tutorials/add-provider/
eyebrow: 开发者教程
description: 几分钟把任意 OpenAI 兼容端点接入 wow-agent —— 预设、请求头、模型列表与能力声明。
---
任何说 OpenAI Chat Completions 方言的端点都能成为 wow-agent 服务商。本教程接入一个虚构服务商 **NebulaAI**。
## 最快路径：零代码
一次性使用不用写代码 —— 设三个环境变量：
```bash
# ~/.wow-agent.env
WOW_API_KEY=neb_sk-...
WOW_BASE_URL=https://api.nebula.ai/v1
WOW_MODEL=nebula-coder-large
```
完成。本教程剩下的部分是把它做成**一等服务商**：选择器入口 + 在线模型列表。
## 第 1 步 —— 加预设
在 `wow_agent/config.py` 扩展 `PROVIDERS`：
```python
"nebula": {
    "base_url": "https://api.nebula.ai/v1",
    "models": ["nebula-coder-large", "nebula-coder-mini"],
    "default": "nebula-coder-large",
    "api_key_env": "NEBULA_API_KEY",      # 从哪个环境变量读 Key
    "capabilities": {
        "streaming": True,
        "tools": True,          # 支持函数/工具调用
        "vision": False,
        "max_context": 128000,
    },
},
```
字段说明：
| 字段 | 必需 | 含义 |
|---|---|---|
| `base_url` | ✔ | OpenAI 兼容根地址（需要 `/v1` 就带上） |
| `models` | ✔ | 静态兜底模型列表 |
| `default` | ✔ | 默认选中模型 |
| `api_key_env` | – | 存 Key 的环境变量名 |
| `headers` | – | 额外请求头，支持 `{api_key}` 占位符 |
| `capabilities` | – | 让 Agent 调整行为（比如不支持工具调用时） |
## 第 2 步 —— 验证
```bash
uv run wow
/model            # 选择器里应出现 NebulaAI
/model nebula     # 快速切换
/model --fetch    # 从端点拉取实时模型列表（如支持）
```
## 第 3 步 —— 处理方言差异（可选）
有的端点略有偏差。`config.py` 服务商条目里常见的补丁：
```python
"headers": {"X-Source": "wow-agent"},          # 追踪头
"query_params": {"api-version": "2024-02-01"}, # Azure 式版本参数
"wire": {"tool_format": "openai_v1"},          # 强制方言
```
## 第 4 步 —— 贡献回上游
1. `uv run python tests_smoke.py` —— 必须保持绿
2. `PROVIDERS` 加条目 + 测试夹具
3. PR 标题用服务商名：`feat(providers): NebulaAI`
完整流程见[参与贡献](/zh/tutorials/contributing/)。
## 故障排查
| 现象 | 可能原因 |
|---|---|
| `401 Unauthorized` | Key 放错环境变量 / 没导出 |
| chat 请求 `404` | `base_url` 少了或多算了 `/v1` |
| 从不调用工具 | `capabilities.tools` 为 false 或方言不匹配 |
| 流式输出乱码 | 设 `capabilities.streaming: false` 强制普通模式 |
