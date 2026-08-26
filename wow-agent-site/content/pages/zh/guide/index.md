---
title: 从这里开始
layout: docs
permalink: /zh/guide/
eyebrow: 用户指南
description: wow-agent 用户友好起点 —— 它是什么、五分钟装好、接下来去哪，不需要任何 Agent 使用经验。
---
欢迎！本指南写给只想**把活干完**的人 —— 不需要任何 Agent 使用经验。
## wow-agent 是什么？一段话说清
它是住在你终端里的编程伙伴。你描述一个目标（"修这个 Bug"、"加这个功能"、"这为什么报错？"），它会**规划**工作、用真实工具**执行**（读文件、改代码、跑测试）、**验证**结果，验证失败时**自动回滚**。模型随便带 —— 云端或本地都行，除非你自己发给云服务商，代码永不离机。
## 五分钟快速通道
```bash
# 1. 拿到它（Linux / macOS / WSL）
git clone https://github.com/uuzjw/wow-agent.git && cd wow-agent
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 装依赖
uv sync

# 3. 启动 —— 向导会帮你配好模型
uv run wow
```
> 所有平台的详细安装（含离线部署）：[安装](/zh/guide/installation/)。
## 两分钟了解安全模型
能执行命令的 Agent 必须被约束。wow-agent 默认开启四层防护：
1. **断网沙盒** —— Agent 的 Shell 上不了网
2. **外传拦截** —— `git push`、`scp`、`curl POST` 被拦截或需确认
3. **高危命令确认** —— `rm -rf /` 这类命令必须输入 `YES`
4. **回滚** —— 每次写文件都有快照，`/undo` 随时撤销
完整原理见[安全系统](/zh/safety/)。现在只需记住：**失败的任务毁不了你的仓库** —— 它会自己滚回来。
## 你的第一个真实任务
阅读[第一个任务](/zh/guide/first-task/) —— 手把手演练，每个界面都展示：计划、执行、验证，以及出问题时怎么办。
## 然后呢
| 我想… | 去看 |
|---|---|
| 复制就能用的提示词 | [日常食谱](/zh/guide/cookbook/) |
| 精通每个命令 | [命令速查](/zh/guide/commands/) |
| 了解模型与成本 | [模型生态](/zh/guide/model-eco/) |
| 搞懂内部原理 | [架构设计](/zh/architecture/) |
| 常见疑虑的解答 | [常见问题](/zh/guide/faq/) |
## Agent 怎么思考（30 秒版）
```text
你给一个目标
  → PLANNING   读相关代码，提出任务树
  → EXECUTING  逐步执行，每次写入打快照
  → VERIFYING  跑你的测试证明结果
  → DONE       或 FAILED → 自动整轮回滚
```
这个循环就是整个产品，其他都是细节。
