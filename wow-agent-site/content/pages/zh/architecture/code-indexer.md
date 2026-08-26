---
title: 代码索引器
layout: docs
permalink: /zh/architecture/code-indexer/
eyebrow: 架构
description: 基于 AST 的 Python 符号表 + 增量更新，IDE 级代码导航。
---

## 提取内容

类、函数、方法（含 async）、装饰器、类型标注、Docstring、导入与交叉引用。

```text
src/services/user_service.py
  class UserService            :15
    __init__                   :18
    async get_user             :22   → UserRepository.find
    async create_user          :31   → User, UserCreate
```

## 查询

```bash
> Symbols *Service              # 按名称模式匹配
> References UserService.get_user
> Definition UserRepository
```

## 增量更新

文件监听器只重算变更文件；内容哈希跳过无变化写入；符号表原子合并。

## 性能

| 操作 | 1 万文件 |
|---|---|
| 首次索引 | ~3 秒 |
| 增量更新 | ~50 毫秒 |
| 符号查询 | ~5 毫秒 |

## 配置

```bash
WOW_INDEX_PATHS=src,lib,tests
WOW_INDEX_EXCLUDE=**/migrations/**
WOW_INDEX_WATCH=1
```
