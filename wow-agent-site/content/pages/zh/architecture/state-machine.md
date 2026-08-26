---
title: 状态机
layout: docs
permalink: /zh/architecture/state-machine/
eyebrow: 架构
description: planning、executing、verifying、done、failed 五状态如何驱动每个任务。
---

```text
planning ──▶ executing ──▶ verifying ──▶ done
                │             │
                ▼             ▼
              failed ◀────────┘   → 自动回滚 → 重试
```

## 状态转换

- **planning → executing** — 计划批准（手动或自动模式）
- **executing → verifying** — 所有子任务完成
- **verifying → done** — 测试/Lint/类型检查通过
- **verifying → failed** — 检查失败；恢复快照
- **any → failed** — 严重错误或达到最大迭代

## 各状态的职责

| 状态 | 关键动作 |
|---|---|
| planning | 查询代码索引、构建任务树、展示计划 |
| executing | 选择就绪子任务、写入前快照、跟踪进度 |
| verifying | 运行测试套件 + Linter + 自定义验证器 |
| done | 总结、清理、更新记忆 |
| failed | 逆序回滚任务全部快照 |

## 调优

```bash
WOW_MAX_ITER=40          # 每任务最大迭代
WOW_ROLLBACK_ON_FAIL=1   # 失败自动回滚
```
