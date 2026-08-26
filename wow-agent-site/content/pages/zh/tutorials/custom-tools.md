---
title: 自定义工具
layout: docs
permalink: /zh/tutorials/custom-tools/
eyebrow: 开发者教程
description: 约 30 行代码教会 wow-agent 新本领 —— Schema、执行器、安全级别与测试的完整实战。
---
本教程给 Agent 加一个 `deploy` 工具，让它能把项目部署到 staging。耗时约 15 分钟。
## 工具的工作原理
一个工具 = **JSON Schema**（模型看到什么）+ **执行器**（实际跑什么）+ **安全级别**（防护层要什么）。模型决定用某个工具时，wow-agent 按 Schema 校验参数、过安全检查、按需打快照，然后调用你的执行器。
## 第 1 步 —— 声明 Schema
打开 `wow_agent/tools.py`，往 `TOOLS_SCHEMA` 里加：
```python
"deploy": {
    "description": (
        "部署当前项目到目标环境。"
        "仅当用户明确要求部署时使用。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "environment": {
                "type": "string",
                "enum": ["staging", "production"],
                "description": "目标环境",
            },
            "version": {
                "type": "string",
                "description": "Git 引用或版本标签；默认 HEAD",
            },
        },
        "required": ["environment"],
    },
    "safety": "modify",       # safe | modify | destructive
    "confirmation": True,      # 总是先问用户
}
```
Schema 技巧：
- `description` 就是提示词工程 —— 写清**何时**用这个工具
- `enum` 防止模型瞎编环境名
- `confirmation: True` 强制交互确认，自动模式也不例外
## 第 2 步 —— 写执行器
```python
async def execute_deploy(params: dict, context) -> dict:
    import subprocess

    env = params["environment"]
    ref = params.get("version", "HEAD")

    result = subprocess.run(
        ["scripts/deploy.sh", env, ref],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        return {"success": False, "error": result.stderr[-2000:]}

    return {
        "success": True,
        "output": result.stdout[-2000:],
        "url": f"https://{env}.example.com",
    }

TOOL_EXECUTORS["deploy"] = execute_deploy
```
执行器契约：
- 接收校验过的 `params` + 执行 `context`
- 返回带 `success` 的字典 —— 错误会回传给模型，让它重试或解释
- 输出限长（`[-2000:]`）—— 巨型输出会烧上下文
## 第 3 步 —— 试跑
```text
You > 把当前 HEAD 部署到 staging

┌ PLANNING
│ 1. 确认部署（需要批准）
│ 2. 执行 deploy 工具 → staging @ HEAD
Approve? [Y/n] y

⚠ 部署到 staging —— 确认？[y/N] y
✔ https://staging.example.com 已上线
```
注意有**双重确认**：计划一次，`confirmation: True` 再一次。
## 第 4 步 —— 不用 LLM 也能测
```python
# tests/test_tool_deploy.py
import asyncio
from wow_agent.tools import TOOL_EXECUTORS

def test_deploy_rejects_bad_env(monkeypatch):
    async def fake_run(*a, **k):
        class R: returncode = 1; stderr = "bad env"; stdout = ""
        return R()
    monkeypatch.setattr("subprocess.run", fake_run)
    result = asyncio.run(TOOL_EXECUTORS["deploy"]({"environment": "staging"}, None))
    assert result["success"] is False
```
离线运行：
```bash
uv run python tests_smoke.py
```
## 检查清单
- [ ] Schema 的 `description` 有用，能用 `enum` 就用
- [ ] 安全级别符合实际（改不改状态？）
- [ ] 输出已截断，上下文友好
- [ ] 加了离线单元测试
- [ ] 沙盒开启时可用（不需要网络，或有说明）
