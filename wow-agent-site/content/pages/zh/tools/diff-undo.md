---
title: Diff 与撤销
layout: docs
permalink: /zh/tools/diff-undo/
eyebrow: 工具
description: 彩色 Diff、单步 /undo、任务级回滚与跨重启快照。
---

## Diff

每次修改都会先渲染统一彩色 Diff：

```diff
- def process_payment(amount):
+ def process_payment(amount: float) -> PaymentResult:
+     if amount <= 0:
+         raise ValueError("Amount must be positive")
```

## 撤销

```bash
/undo                # 撤销最近修改
/undo 3              # 最近三步
/undo --list         # 带时间戳的历史
/undo --to=snap_abc  # 恢复到指定快照
/undo --dry-run      # 仅预览
```

## 自动回滚

验证阶段失败时，**任务的全部快照按逆序恢复**，任务期间创建的文件被删除。

```text
任务"添加认证"
├── ✔ 模型已创建        (snap_1)
├── ✔ 端点已添加        (snap_2)
├── ✘ 测试失败
└── ↩ 回滚 → 仓库回到任务前状态
```

## 存储

快照保存在 `~/.wow-agent/snapshots/`（Diff + 元数据），跨重启有效，上限 `WOW_MAX_SNAPSHOTS`（默认 1000）、保留 30 天。
