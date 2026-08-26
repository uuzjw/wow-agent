---
title: Code Indexer
layout: docs
permalink: /architecture/code-indexer/
eyebrow: Architecture
description: AST-based Python symbol table with incremental updates — IDE-grade navigation.
---

## What it extracts

Classes, functions, methods (async included), decorators, type hints, docstrings, imports and cross-references.

```text
src/services/user_service.py
  class UserService            :15
    __init__                   :18
    async get_user             :22   → UserRepository.find
    async create_user          :31   → User, UserCreate
```

## Queries

```bash
> Symbols *Service              # glob over symbol names
> References UserService.get_user
> Definition UserRepository
```

## Incremental updates

A file watcher recomputes only changed files; content hashes skip no-op writes and the symbol table is merged atomically.

## Performance

| Operation | 10k files |
|---|---|
| initial index | ~3 s |
| incremental | ~50 ms |
| symbol query | ~5 ms |

## Config

```bash
WOW_INDEX_PATHS=src,lib,tests
WOW_INDEX_EXCLUDE=**/migrations/**
WOW_INDEX_WATCH=1
```
