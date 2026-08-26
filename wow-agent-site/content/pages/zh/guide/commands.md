---
title: 命令参考
layout: docs
permalink: /zh/guide/commands/
eyebrow: 指南
description: wow-agent 全部斜杠命令、Shell 直通与快捷键。
---

## 核心

| 命令 | 说明 |
|---|---|
| `/help` | 列出所有命令 |
| `/model [id]` | 切换服务商/模型；`--list`、`--fetch`、`--info` |
| `/status` | 上下文用量、任务进度、可撤销改动 |
| `/compact [要求]` | 压缩对话历史 |
| `/clear` | 清空对话 |
| `/exit` | 退出 |

## 记忆

```bash
/mem save "project:auth" "JWT 在 src/auth/"
/mem use "project:auth"
/mem list
/mem rm "project:old"
```

## 审查与安全

```bash
/review src/auth/ --level=high   # 安全向审查
/safe status                     # 沙盒 + 外传状态
/safe logs                       # 最近安全事件
/undo                            # 单步撤销
/undo 3                          # 撤销最近三步
/undo --to=snap_abc123           # 恢复到快照
```

## Shell 直通

```bash
!git status          # 立即执行，不经过模型
!pytest -x tests/    # 输出实时流入会话
```

## 别名

`/h` → help · `/m` → model · `/s` → status · `/u` → undo · `/r` → review
