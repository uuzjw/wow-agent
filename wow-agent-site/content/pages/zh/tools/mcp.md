---
title: MCP 集成
layout: docs
permalink: /zh/tools/mcp/
eyebrow: 工具
description: 用 Model Context Protocol 服务器扩展代理 —— 文件系统、GitHub、数据库与自建服务。
---

## 配置

`~/.wow-agent/mcp.json`：

```json
{
  "servers": {
    "fs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fs", "/tmp"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_xxx" }
    }
  }
}
```

## 工作方式

启动时代理拉起每个服务器、发现其工具并注册为 `mcp_<服务器>_<工具>`。之后模型可以像调用内置工具一样调用它们。

## 安全

- MCP 服务器继承代理的网络沙盒
- 文件系统服务器只挂载窄目录
- 锁定版本：`server-github@1.2.3`

## 调试

```bash
/debug mcp        # 服务器状态（运行中/失败）
/mcp refresh      # 重连 + 重新发现工具
```
