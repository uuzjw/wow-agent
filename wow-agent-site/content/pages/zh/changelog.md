---
title: 更新日志
layout: docs
permalink: /zh/changelog/
eyebrow: 产品
description: wow-agent 发布历史 —— 每个版本发布了什么，最新在前。
---
格式遵循 [Keep a Changelog](https://keepachangelog.com/)；版本遵循 [SemVer](https://semver.org/)。
## v0.6.0 —— 当前版本
**安全与规模化版本。**
### 新增
- 四层安全系统：`unshare -n` 断网沙盒、外传拦截（`curl POST`/`scp`/`git push`/`npm publish`）、高危命令二次确认、快照回滚
- `/review` 三级代码审查（🔴 高 / 🟡 中 / 🟢 低），由审查子代理驱动
- AST 代码索引：符号、引用、定义，增量更新
- 长期记忆：`/mem save/use/rm/list/new`
- MCP 客户端：运行任意 Model Context Protocol 服务器，工具自动发现
- 双语界面（中/英），`/language` 切换
- ARM64 支持，Jetson Orin NX 实测
### 变更
- 状态机强化：失败任务自动回滚全部快照
- `/model --fetch` 从服务商在线拉取模型列表
- 会话持久化改进：跨重启 `/resume`
### 性能
- Agent 冷启动一秒内
- 索引增量更新约 50 毫秒/文件
## v0.5.0
### 新增
- 子代理系统：全新上下文的调研代理 + 结构化结果
- 每次文件修改的 Diff 可视化
- `/compact [提示]` 引导式历史压缩
### 修复
- 快照跨会话完整性（`/undo --verify`）
## v0.4.0
### 新增
- 服务商预设：DeepSeek、Qwen、Kimi、GLM、SiliconFlow、OpenAI、Gemini、Ollama、LM Studio
- `/model --fetch` 在线模型列表
- Shell 直通 `!命令`（带安全检查）
## v0.3.0
### 新增
- 任务树规划 + 用户批准
- 基于快照的 `/undo`（单步与多步）
- `/status` 仪表盘
## v0.2.0
### 新增
- 工具调用循环 + JSON Schema 校验
- 文件工具：read/write/edit/delete/list/glob/grep
- Shell 工具带超时控制
## v0.1.0
- 首个公开版本：交互终端 REPL、OpenAI 兼容对话、基础规划
---
更早的详情见 [GitHub Releases](https://github.com/uuzjw/wow-agent/releases)。
