---
title: 子代理系统
layout: docs
permalink: /zh/architecture/sub-agents/
eyebrow: 架构
description: 隔离的调研与审查代理，保持主上下文干净。
---

## 为什么

调研非常烧上下文。子代理运行在**干净上下文**中、只用只读工具，返回结构化摘要 —— 主代理只看到结论，看不到噪音。

## 类型

| 类型 | 工具 | 返回 |
|---|---|---|
| 调研 | read · grep · symbols · index | 总结 + 关键文件 + 建议 |
| 审查 | 只读 | 🔴高风险 / 🟡建议 / 🟢优化 问题清单 |

## 流程示例

```text
主代理："我需要理解支付流程"
  └─▶ 生成调研代理（全新上下文）
        读 payment/*.py、搜 "webhook"、查符号表
      ◀─ 摘要："Stripe + 幂等键；见 service.py:45 …"
主代理：带着结论继续规划，零污染
```

## 用法

```bash
/review src/payment/ --level=high
> 调研：缓存失效是怎么实现的？
```

并发有上限（`WOW_MAX_SUBAGENTS=3`），每个子代理有独立超时。
