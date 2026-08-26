---
title: 回滚系统
layout: docs
permalink: /zh/safety/rollback/
eyebrow: 安全 · 第 4 层
description: 基于快照的撤销，跨重启有效，失败任务自动整体还原。
---

## 手动撤销

```bash
/undo                  # 撤销最近修改
/undo 3                # 最近三步
/undo --list           # 可撤销内容
/undo --to=snap_xxx    # 恢复到指定时间点
/undo --all            # 整个会话
/undo --dry-run        # 仅预览
```

## 自动回滚

验证阶段任务失败时触发全量回滚：快照逆序恢复、任务创建的文件删除、目录清理。

## 快照

```json
{
  "id": "snap_a1b2c3d4",
  "operation": "edit",
  "target": "src/auth.py",
  "diff": "@@ -10,7 +10,12 @@ …"
}
```

- 存储于 `~/.wow-agent/snapshots/`
- 跨重启持久
- `WOW_MAX_SNAPSHOTS=1000`、保留 30 天
- `/undo --verify` 检查完整性

## 建议

1. 高风险操作前打标签：`/snapshot create "重构前"`
2. 不确定时先 `--dry-run`
3. 里程碑节点配合 git 提交
