---
title: 第一个任务
layout: docs
permalink: /zh/guide/first-task/
eyebrow: 用户指南
description: 手把手带你完成 wow-agent 的第一个真实编码任务 —— 从输入目标到验证通过，每一步界面都展示给你看。
---
本教程带你完整走一遍真实任务：**"给函数加上输入校验，并修复你发现的 Bug"**。你看到的每个界面都会展示出来。
## 1. 启动 Agent
```bash
cd my-project
uv run wow
```
会询问 `Enter auto mode? y/N`：
- **N（默认，首次推荐）**—— Agent 展示计划，写入前先征得同意
- **y**—— 跳过逐步确认自动执行；高危命令和数据外传*仍然*需要批准
## 2. 描述目标，而不是步骤
```text
You > src/config.py 里的 parse_config 在文件有重复键时崩溃。
      找出原因并妥善修复。
```
好提示词的技巧：
- ✅ 说清**哪里有问题**（哪怕是大致位置）
- ✅ 说清"修好"对你意味着什么
- ❌ 别指挥具体改哪一行 —— 规划是 Agent 的工作
## 3. 看计划（PLANNING 状态）
Agent 通过代码索引读取相关文件，然后展示任务树：
```text
┌ PLANNING ───────────────────────────────────────────┐
│ 1. 读取 src/config.py 并复现崩溃                    │
│ 2. 定位根因（重复键处理）                            │
│ 3. 实施修复 + 补回归测试                             │
│ 4. 运行测试套件                                      │
│ Approve plan? [Y/n]                                  │
└──────────────────────────────────────────────────────┘
```
按 **Y** 批准。想先改计划？输 `n` 再补充，比如 `合并重复键时打警告日志`。
## 4. 执行（EXECUTING 状态）
Agent 逐个完成子任务。**每次**写文件前都会打快照（这就是 `/undo` 的底气）：
```text
┌ EXECUTING 2/4 ──────────────────────────────────────┐
│ ▸ 读取 src/config.py（48 行）                        │
│ ✔ 根因：load() 第 31 行 dict 直接覆盖               │
│ ▸ 编辑 src/config.py                                 │
│   @@ -28,7 +28,12 @@                                 │
│   -    data = json.load(f)                           │
│   +    data = json.load(f, object_pairs_hook=...)    │
│ snapshot snap_4f2a saved                             │
└──────────────────────────────────────────────────────┘
```
## 5. 验证（VERIFYING 状态）
实现完成后，Agent 会**证明**它：
```text
┌ VERIFYING ──────────────────────────────────────────┐
│ ✔ pytest tests/test_config.py -q   12 passed        │
│ ✔ ruff check .                     clean            │
│ Task complete in 3m 41s                             │
└──────────────────────────────────────────────────────┘
```
## 6. 出问题怎么办
```text
You > /undo          # 撤销最近一次修改
You > /undo --list   # 查看所有可撤销项
```
如果验证失败，wow-agent 会**自动整轮回滚** —— 仓库精确回到任务前状态，并给你错误报告。
## 7. 收尾
```text
You > /status        # 上下文占用、任务进度
You > !git diff      # 亲眼检查变更
You > !git add -A && git commit -m "fix: parse_config 重复键崩溃"
```
## 你刚学到的概念
| 概念 | 含义 |
|---|---|
| 状态机 | planning → executing → verifying → done/failed |
| 快照 | 每次写入都可经 `/undo` 撤销 |
| 验证 | 测试/Lint 通过才算"完成" |
| 自动回滚 | 失败任务自动还原仓库 |
## 接下来
- [日常食谱](/zh/guide/cookbook/) —— 10+ 现成配方
- [命令速查](/zh/guide/commands/) —— 完整斜杠命令工具箱
