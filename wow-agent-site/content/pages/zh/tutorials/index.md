---
title: 开发者教程
layout: docs
permalink: /zh/tutorials/
eyebrow: 开发者
description: wow-agent 扩展开动手把手教程 —— 自定义工具、模型服务商、MCP 服务器、子代理与参与贡献。
---
wow-agent 生来可扩展。每一层都暴露干净的扩展点，选你的路线：
## 学习路径
| 我想… | 教程 | 难度 |
|---|---|---|
| 给 Agent 新能力（部署、查内部 API 等） | [自定义工具](/zh/tutorials/custom-tools/) | ★☆☆ |
| 接入内置之外的服务商 | [添加服务商](/zh/tutorials/add-provider/) | ★☆☆ |
| 用 MCP 接外部能力（文件、GitHub、数据库） | [MCP 服务器](/zh/tutorials/mcp-servers/) | ★★☆ |
| 理解并开发隔离的调研/审查代理 | [子代理开发](/zh/tutorials/subagents/) | ★★☆ |
| 修 wow-agent 本体的 Bug / 加功能 | [参与贡献](/zh/tutorials/contributing/) | ★★☆ |
## 30 秒心智模型
```text
你 ──▶ 智能核心（规划、决策）
           │ 调用
           ▼
        工具  ← Agent 能"做"的一切都在这里
           │
     ┌─────┼──────┐
     ▼     ▼      ▼
   内置   自定义   MCP      ← 你的扩展点
  (read/  (你的   (外部
   edit/…) schema) 服务)
```
三条路径，按投入排序：
1. **MCP 服务器** —— 零 wow-agent 代码，跑任意标准 MCP 服务即可
2. **自定义工具** —— `tools.py` 里约 30 行 Python
3. **核心贡献** —— 改 Agent 本体，见[参与贡献](/zh/tutorials/contributing/)
## 扩展的三条铁律
- 工具必须声明**安全级别**（`safe` / `modify` / `destructive`）—— 安全系统强制执行
- 所有 I/O 走工具层，快照与日志自动覆盖你的代码
- 参数用 JSON Schema 校验 —— 模型负责填，校验负责防
从[自定义工具](/zh/tutorials/custom-tools/)开始 —— 大多数人 15 分钟搞定。
