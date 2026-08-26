---
title: 智能核心
layout: docs
permalink: /zh/guide/agent-brain/
eyebrow: 核心概念
description: 任务规划、planning→executing→verifying 状态机与干净上下文子代理。
---

## 任务规划

高层目标自动拆解：

```
目标："添加 JWT 认证"
├── 调研现有认证模式
├── 设计 Token 模式
├── 实现模型 + 中间件
├── 添加登录/注册端点
└── 编写测试、更新文档
```

非自动模式下，计划会先展示供你批准。

## 状态机

```text
planning → executing → verifying → done
                ↘            ↗
                 failed ←────┘   （自动回滚）
```

| 状态 | 做什么 |
|---|---|
| planning | 通过代码索引分析仓库、构建任务树 |
| executing | 调用工具，每次写入前快照 |
| verifying | 运行测试/Lint/类型检查 |
| failed | 整轮回滚 + 错误报告 |

## 子代理

- **调研代理** — 干净上下文、只读工具，只回结论不污染主上下文
- **审查代理** — 驱动 `/review` 三级审查（🔴高风险 · 🟡建议 · 🟢优化）

## 记忆

短期历史在 `WOW_AUTO_COMPACT` Token 时自动压缩。长期知识跨会话持久：

```bash
/mem save "project:payment" "Stripe webhook 在 payment/webhooks.py"
```
