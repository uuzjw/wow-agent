---
title: 子代理开发
layout: docs
permalink: /zh/tutorials/subagents/
eyebrow: 开发者教程
description: wow-agent 隔离子代理的工作原理、生成时机，以及如何在提示词和代码里用好它们。
---
子代理解决一个问题：**调研烧上下文**。子代理拿到全新上下文、只读工具，只回传结论。
## 模型
```text
主代理（全上下文，全部工具）
   │ spawn(query, scope)
   ▼
子代理（全新上下文，只读：read/grep/symbols/index）
   │ 自由探索 —— 过程不进主上下文
   ▼
结构化结果: { summary, key_files[], findings[], recommendations[] }
```
## 什么时候会生成
- 提示词里出现**调研/研究/investigate**
- 计划中的某一步是纯信息收集
- 调用 `/review`（审查子代理，只读）
转写里会看到：
```text
▸ 生成调研子代理（全新上下文）
  … 14 次文件读取、6 次符号查询（对主上下文隐藏）
◀ 调研完成 —— 摘要：3 个关键文件，2 条建议
```
## 驱动子代理的技巧
```text
# 好：有边界的问题 + 期望的输出形式
> 调研：写入之后缓存失效是怎么触发的？
  列出涉及的具体函数和调用位置。

# 好：对比式调研
> 调研：src/auth/ 的认证中间件和 examples/ 里的模式
  有什么不同？用表格汇报差异。

# 差：漫无目的
> 调研一下代码库
```
## 子代理不能做什么
- 写、改、删（只读工具集）
- 执行 Shell 命令
- 看到你的对话历史 —— **所有上下文必须在查询里说明**
## 配置
```bash
WOW_MAX_SUBAGENTS=3      # 并发上限
WOW_SUBAGENT_TIMEOUT=120 # 每次生成超时（秒）
WOW_SUBAGENT_MODEL=auto  # 同模型 | 调研用更快的模型
```
## 扩展（代码层）
`wow_agent/subagent.py` 暴露生成器：
```python
result = await subagent_manager.spawn(
    type="research",            # research | review
    query="feature flags 在哪里被读取？",
    scope=Path("src/"),         # 限制探索范围
    constraints=["忽略 tests/"],
)
result.summary        # 2–3 句答案
result.key_files      # [FileRef(path, line)]
result.recommendations
```
结果是 dataclass —— 可以安全地喂进规划提示词。
## 设计笔记
- 每次生成全新上下文：调研任务之间零污染
- Token 记账：子代理开销单独统计，`/status` 可见
- 失败廉价：超时的子代理返回部分发现，绝不阻塞主任务
