---
title: 常见问题
layout: docs
permalink: /zh/guide/faq/
eyebrow: 用户指南
description: 新用户最关心的问题 straight answers —— 模型、隐私、安全、成本与日常使用。
---
## 需要 API Key 吗？
不一定。安装时选 **Ollama** 或 **LM Studio**，全部本地运行，零 Key。云服务商需要各自的 Key。
## 我的代码会传到哪里？
不传，除非你选择云端模型。本地模型时推理发生在你机器上，什么都不外发。云端模型时只有你批准的上下文会发给该服务商。Agent 本体**没有任何遥测**。
## 让它执行命令安全吗？
默认有三层保护：
1. **断网沙盒** —— Agent 的 Shell 无法访问网络
2. **外传拦截** —— `git push`、`scp`、`curl POST`、`npm publish` 被拦截或需确认
3. **高危命令确认** —— `rm -rf /`、`dd`、fork bomb 必须手动输入 `YES`
另外每次文件写入都有快照：`/undo` 随时撤销。
## 要花多少钱？
Agent 本身免费（MIT）。模型成本看服务商：
- **免费**：Ollama / LM Studio（用自己的硬件）、OpenCode Zen 免费档
- **便宜**：DeepSeek、Qwen 的免费/低价档足够日常编程
- 按量付费 —— 没有订阅、没有按座位收费
## 第一次用选什么模型？
| 场景 | 推荐 |
|---|---|
| 先试试 | OpenCode Zen 免费档 |
| 隐私优先 | Ollama `deepseek-coder:6.7b` |
| 质量最好 | DeepSeek `deepseek-coder` 或 GPT-4o |
| 机器配置低 | Qwen 小参数档（走 API） |
## 和浏览器里的 ChatGPT/Claude 有什么区别？
它们是"聊"代码；wow-agent **在你的仓库里干活**：用代码索引读文件、带 Diff 改文件、跑测试、验证结果、失败回滚。它工作在代码所在的地方。
## 和 IDE 副驾驶有什么区别？
副驾驶在编辑器里补全代码。wow-agent 是**任务 Agent**：你给目标（"修这个 Bug"），它规划、改多个文件、跑验证、汇报结果。是不同层面的工具。
## 公司里能用吗？
可以 —— MIT 协议。安全默认（沙盒 + 外传拦截）适合专有代码。严格合规场景可用本地模型完全离线运行。
## 支持 Windows / ARM 吗？
- **Windows**：PowerShell，实验性
- **macOS**：原生（含 Apple Silicon）
- **Linux**：主力平台
- **ARM64**：一等公民 —— Jetson Orin NX 实测
## Agent "失败"了 —— 我的仓库坏了吗？
几乎不会。失败任务触发**自动回滚**：该任务的所有快照逆序恢复。查看 `/safe logs` 了解记录，`/undo --list` 随时可用。
## 上下文快满了怎么办？
```text
/compact              # 立即压缩历史
/compact 保留认证相关  # 压缩时保留指定内容
```
到达 `WOW_AUTO_COMPACT` Token 会自动压缩。长期知识用 `/mem save`。
## 怎么报 Bug / 提需求？
[GitHub Issues](https://github.com/uuzjw/wow-agent/issues) —— 欢迎 PR，见[参与贡献](/zh/tutorials/contributing/)。
