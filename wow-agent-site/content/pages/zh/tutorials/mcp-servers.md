---
title: MCP 服务器
layout: docs
permalink: /zh/tutorials/mcp-servers/
eyebrow: 开发者教程
description: 用 Model Context Protocol 服务器零代码扩展 wow-agent —— 文件系统、GitHub、数据库或你自己的服务。
---
MCP（Model Context Protocol）是向 LLM Agent 暴露**工具**与**资源**的标准协议。wow-agent 原生支持：配置一次服务器，它的工具就和内置工具并列出现。
## 第 1 步 —— 配置
创建 `~/.wow-agent/mcp.json`：
```json
{
  "servers": {
    "fs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/me/projects"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_xxx" }
    }
  }
}
```
每个服务器 = 进程命令 + 参数 + 可选环境变量。Agent 启动时拉起它们。
## 第 2 步 —— 验证发现
```text
You > /debug mcp
  fs      RUNNING   tools: read_file, write_file, list_directory, …
  github  RUNNING   tools: create_issue, get_pull_request, …

You > /debug tools          # mcp_fs__read_file 等已列出
```
工具命名空间为 `mcp_<服务器>__<工具>`，永不与内置冲突。
## 第 3 步 —— 使用
自然语言直接说 —— 模型看得到工具 Schema：
```text
You > 列出 uuzjw/wow-agent 仓库带 "bug" 标签的开放 issue
You > 读一下 /home/me/projects/notes/roadmap.md 并总结
```
## 自己写一个 MCP 服务器（Python）
```python
# my_server.py  —  pip install "mcp[cli]"
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("team-tools")

@mcp.tool()
def oncall_schedule() -> str:
    """返回本周值班工程师。"""
    return "alice（周一至周三），bob（周四、周五）"

@mcp.tool()
def query_status(service: str) -> str:
    """查询某服务的内部状态页。"""
    return f"{service}: 一切正常"

if __name__ == "__main__":
    mcp.run()
```
注册：
```json
{
  "servers": {
    "team": { "command": "python", "args": ["/path/to/my_server.py"] }
  }
}
```
## 安全模型
- MCP 服务器**继承 Agent 的断网沙盒** —— 恶意服务器也无法外联
- 文件系统服务器只能看到 `args` 里给的路径 —— 挂载范围尽量窄
- 工具调用照样过安全系统（`destructive` 确认照常生效）
- 锁版本防供应链风险：`server-github@1.2.3`
## 运维
```bash
/debug mcp          # 各服务器状态（运行中 / 失败 + stderr）
/mcp refresh        # 重启服务器并重新发现工具
```
## 故障排查
| 现象 | 处理 |
|---|---|
| 启动时 FAILED | 手动运行它的命令，看 stderr |
| 工具没出现 | `/mcp refresh`；检查 `npx` 可用性 |
| 启动慢 | 去掉不用的重型包；锁版本利用缓存 |
