---
title: CLI 命令大全
layout: docs
permalink: /zh/cli/
eyebrow: 参考手册
description: wow-agent 完整命令参考 —— 每个斜杠命令、参数、Shell 直通与快捷键，含语法、示例与预期输出。
---
这是 wow-agent 里你能输入的一切的详尽参考。想按任务学，请看[日常食谱](/zh/guide/cookbook/)。
## 启动参数
```bash
uv run wow [options]
```
| 参数 | 效果 |
|---|---|
| *（无）* | 交互会话，逐步确认 |
| `--auto` | 自动模式：计划自动批准（高危/外传仍需确认） |
| `--model <id>` | 指定模型启动，如 `--model deepseek` 或 `--model ollama:llama3` |
| `--language en\|zh` | 本次会话覆盖界面语言 |
| `--safe 0` | 本次会话关闭沙盒（不推荐） |
---
## 斜杠命令
### `/help`
列出所有命令及一行说明。别名：`/h`、`?`。
### `/model`
模型控制中心。
```text
/model              交互选择器：服务商 → 模型
/model deepseek     按服务商 ID 快速切换
/model ollama:qwen2.5-coder:7b   服务商:模型 语法
/model --list       显示当前服务商的模型
/model --fetch      从服务商 API 刷新列表
/model --info       当前模型、上下文大小、能力
```
任务中途切换模型是安全的 —— 对话上下文保留。
### `/status`
仪表盘。一目了然：
```text
Session ─────────────────────────────
 Context    38,412 / 128,000 (30%)
 Task       fix-auth (EXECUTING, 3/5 子任务)
 Undoable   4 个快照
 Safety     沙盒 ON · 外传拦截 ON
 Model      deepseek-coder (128k ctx)
```
### `/compact [提示]`
压缩对话历史，回收上下文。
```text
/compact                    # 自动摘要压缩
/compact 保留认证重构的细节
/compact --aggressive       # 最大压缩
```
到达 `WOW_AUTO_COMPACT` Token 会自动触发。提示词引导摘要保留什么。
### `/undo`
工作目录的时间机器。
```text
/undo                # 撤销最近一次
/undo 3              # 撤销最近 3 次
/undo --list         # 带快照 ID 的历史
/undo --to=snap_4f2a # 恢复到指定时点
/undo --all          # 撤销本会话全部
/undo --dry-run      # 预览不动文件
```
快照跨重启保留（见[回滚系统](/zh/safety/rollback/)）。
### `/review [路径] [--level=…]`
审查子代理执行的只读代码审查。绝不修改文件。
```text
/review                          # 全项目，中等级别
/review src/auth/                # 限定范围
/review --changed                # 只看未提交改动
/review --level=high             # 🔴 只看安全/正确性
/review --level=low --format=markdown --output=review.md
```
级别：`high` 🔴 安全与正确性 · `medium` 🟡 最佳实践（默认）· `low` 🟢 打磨与性能。
### `/mem`
跨会话的长期记忆。
```text
/mem save "project:auth" "JWT 在 src/auth/，refresh token 存 Redis"
/mem use "project:auth"     # 加载进当前上下文
/mem list                   # 全部，最新在前
/mem rm "project:old"       # 删除
```
Key 按惯例命名空间化：`project:*`、`team:*`、`research:*`。
### `/safe`
```text
/safe              # 总安全开关
/safe status       # 各层状态
/safe logs         # 近期事件：拦截、确认、回滚
/safe test         # 四层自检
```
### `/resume`
```text
/resume            # 交互选择历史会话
/resume --latest   # 直接恢复最近一次
```
### `/snapshot create <标签>`
命名检查点，之后可 `/undo --to` 回来 —— 高风险操作前先打一个。
### `/config [get|set|reset]`
```text
/config                     # 输出生效配置
/config get WOW_MAX_ITER
/config set WOW_MAX_ITER 60 # 仅本会话生效
/config reset               # 恢复默认
```
### `/language [en|zh]`
立即切换界面语言。不带参数：交互菜单。
### `/clear` 与 `/exit`
`/clear` 清空对话（文件不动，需确认）。`/exit` 保存会话退出。别名：`/q`、Ctrl+D。
---
## Shell 直通 `!`
`!` 开头的内容**不经过模型**直接在 Shell 执行：
```text
!git status
!pytest -x -q
!docker compose logs -f api
```
- 输出实时流入会话（为上下文安全做了截断）
- 显示退出码；你让 Agent 看时它能看到
- Shell 命令照样过**安全系统**（沙盒/外传/高危防护都生效）
## 快捷键
| 按键 | 动作 |
|---|---|
| `Tab` | 模糊补全斜杠命令 |
| `↑ / ↓` | 提示历史 |
| `Ctrl+C` | 取消当前 Agent 操作 |
| `Ctrl+D` | 退出 |
| `Ctrl+L` | 重绘屏幕 |
| `Esc` | 关闭菜单/建议 |
## 退出码（脚本场景）
| 码 | 含义 |
|---|---|
| `0` | 正常退出 |
| `1` | 服务商/配置错误 |
| `2` | 安全防护拦截了必要操作 |
| `130` | 用户中断（Ctrl+C） |
