---
title: 文件操作
layout: docs
permalink: /zh/tools/file-ops/
eyebrow: 工具
description: read、write、edit、delete、glob 与 list —— 每次修改都有快照。
---

## 读取

```bash
> Read src/main.py            # 整个文件
> Read src/main.py:10-50      # 行范围
```

## 编辑（精确替换）

```bash
> Edit src/user.py
# 找到:    "def get_user(id):"
# 替换:    "def get_user(id: int) -> User:"
```

`old_string` 必须精确匹配 —— 包含足够的上下文保证唯一。应用前会显示彩色 Diff。

## 写入与删除

- `write` 创建或覆盖；覆盖前先快照
- `delete` 总是需要确认

## 搜索

```bash
> Grep "TODO" --include="*.py"
> Glob "src/**/test_*.py"
> Symbols *Service            # 走代码索引，比 grep 快
```

每个修改类操作都会自动创建回滚快照。
