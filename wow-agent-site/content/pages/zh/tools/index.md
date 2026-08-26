---
title: 工具总览
layout: docs
permalink: /zh/tools/
eyebrow: 参考手册
description: 文件操作、搜索、Diff/Undo、Shell 与 MCP —— 代理的双手。
---

| 类别 | 工具 | 安全级别 |
|---|---|---|
| 文件 | `read` `write` `edit` `delete` `list` `glob` | 安全 → 破坏性 |
| 搜索 | `grep` `symbols` `references` `definition` | 安全 |
| 代码 | `index` `diff` `patch` | 安全 / 修改 |
| 系统 | `shell` `git` | 受安全系统管控 |

## 执行管线

```text
参数校验 → 安全检查 → 快照 → 执行 → 验证 → 返回结果
                          │            │
                          └── 回滚 ◀───┘ （失败时）
```

## 添加自定义工具

```python
TOOLS_SCHEMA["deploy"] = {
    "description": "部署到 staging",
    "parameters": {...},
    "safety": "modify",
}
async def execute_deploy(params, ctx): ...
```

深入阅读：[文件操作](/zh/tools/file-ops/) · [Diff 与撤销](/zh/tools/diff-undo/) · [MCP 集成](/zh/tools/mcp/)
