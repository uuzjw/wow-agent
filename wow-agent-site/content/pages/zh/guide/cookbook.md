---
title: 日常食谱
layout: docs
permalink: /zh/guide/cookbook/
eyebrow: 用户指南
description: 人们真正交给 wow-agent 的任务配方 —— 探索代码、修 Bug、加功能、写测试、审查、重构，直接复制就能用。
---
十个验证过的配方。每条都是可以直接改写使用的提示词 —— 不讲道理，只讲好用。
## 1. 快速读懂陌生代码库
```text
> 带我逛一遍这个仓库：入口、主要模块、数据怎么在模块间流动。
  控制在 30 行以内。
```
*为什么有效：限定了篇幅，答案保持可读。*
## 2. 定位某件事发生在哪
```text
> 用户权限校验在哪里？列出所有能拒绝请求的代码路径，
  带 文件:行号 引用。
```
## 3. 修 Bug（带复现）
```text
> Bug：上传 0 字节文件会产生脏数据。
  1. 先写一个能复现的失败测试
  2. 修复 Bug
  3. 给我看 Diff 并跑全量测试
```
*Agent 会 规划 → 测试先行 → 修复 → 验证。这个顺序免费附赠回归保护。*
## 4. 端到端加功能
```text
> 添加 DELETE /api/v1/items/{id} 端点：
  - 不存在返回 404，成功返回 204
  - 用现有的 require_role 装饰器做权限校验
  - repository + service + handler 分层，风格对齐现有代码
  - 两种结果都要有测试
```
## 5. 给遗留代码补测试
```text
> tests/ 里没有 src/billing/ 的测试。为 InvoiceService 写单元测试：
  覆盖正常路径、按比例计费的边界情况、TODO 注释里提到的货币舍入 Bug。
  数据库层用 mock。
```
## 6. 安全重构
```text
> src/legacy/parser.py 有 900 行。拆到 src/parsing/ 下的多个模块，
  不改变公开行为。前后各跑一次测试套件；不要动 API。
```
*"不改变公开行为"是关键短语 —— 它定义了验证标准。*
## 7. 推代码前先审查
```text
/review --changed --level=high
```
只看安全与正确性，针对未提交的改动。三级完整审查：`/review src/module/`。
## 8. 解释神秘报错
```text
> pytest 报 "RuntimeError: coroutine was never awaited"，
  在 test_orders.py。解释原因并修复所有出现的地方。
```
## 9. 依赖与升级
```text
> 把 requirements.txt 升级到 SQLAlchemy 2.x。
  迁移有变化的查询写法，跑测试，
  列出你注意到的所有行为差异。
```
## 10. 生成项目文档
```text
> 写 docs/API.md：所有公开端点、用测试夹具里的真实请求/响应示例、
  错误码表。语气对齐 README.md。
```
## 通用提示词模式
| 模式 | 示例 |
|---|---|
| **约束** | "不改公开 API"、"不加新依赖" |
| **完成定义** | "测试通过、Lint 干净" |
| **风格锚点** | "风格对齐 src/services/user.py" |
| **步骤排序** | "先写测试再修" |
| **范围围栏** | "只动 src/auth/，别的都别碰" |
## 高手组合技
```text
# 晨间巡检
/review --changed --level=high
> 跑全量测试并总结失败项

# 开 PR 之前
> 为当前暂存区写一条 conventional-commit 提交信息
> 为 PR 描述总结这个 Diff，并列出风险点
```
