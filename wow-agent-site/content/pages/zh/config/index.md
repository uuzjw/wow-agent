---
title: 配置参考
layout: docs
permalink: /zh/config/
eyebrow: 参考手册
description: 全部 WOW_* 环境变量、MCP 服务器与服务商配置。
---

配置文件：`~/.wow-agent.env`（权限 600）。

```bash
WOW_API_KEY=            # API Key
WOW_BASE_URL=           # OpenAI 兼容端点
WOW_MODEL=              # 模型 ID
WOW_SAFE_MODE=1         # 0 关闭沙盒（不推荐）
WOW_MAX_ITER=40         # 每任务最大迭代轮数
WOW_AUTO_COMPACT=55000  # 自动压缩阈值（Token）
WOW_LANGUAGE=en         # en | zh，默认 en
WOW_MODEL_CTX=128000    # 模型上下文长度（用于估算）
WOW_CELL_ASPECT=2.0     # 终端字符宽高比（logo 缩放）
WOW_UPLOAD_GUARD=1      # 外传防护开关
```

## MCP 服务器

`~/.wow-agent/mcp.json`：

```json
{
  "servers": {
    "fs": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-fs", "/tmp"] }
  }
}
```

## 优先级

CLI 参数 → `~/.wow-agent.env` → 项目 `.env` → 内置默认值。

运行时查看：`/config`、`/config get WOW_MAX_ITER`、`/config set WOW_MAX_ITER 60`（仅当前会话）。
