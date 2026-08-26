---
title: 安全系统
layout: docs
permalink: /zh/safety/
eyebrow: 安全
description: 四层防护 —— 断网沙盒、外传拦截、高危命令确认与回滚。
---

```text
第 1 层 · 断网沙盒        unshare -n 网络隔离
第 2 层 · 外传拦截         拦截 curl POST / scp / git push / npm publish
第 3 层 · 高危命令确认     rm -rf / dd / fork bomb 强制二次确认
第 4 层 · 回滚            /undo + 任务失败自动回滚
```

## 快速检查

```bash
/safe status       # 沙盒 + 拦截状态
/safe logs         # 最近事件（拦截、确认、回滚）
/safe test         # 全层自检
```

## 威胁模型

| 威胁 | 缓解 |
|---|---|
| 数据外泄 | 沙盒 + 外传模式匹配 |
| 代码窃取 | 本地执行 + 外传拦截 |
| 破坏性操作 | 输入 `YES` 确认 |
| 变更损坏 | 快照 + 自动回滚 |

安全系统无法防止逻辑 Bug 或社工 —— 输入 `YES` 前请先审阅确认内容。

深入阅读：[断网沙盒](/zh/safety/network-sandbox/) · [回滚系统](/zh/safety/rollback/)
