---
title: 高危命令防护
layout: docs
permalink: /zh/safety/dangerous-commands/
eyebrow: 安全 · 第 3 层
description: 破坏性命令的输入 YES 确认 —— 内置模式、自定义规则，以及为什么确认是最后一道防线。
---
第 3 层拦截会摧毁数据或系统的命令。它故意"烦人"：这些命令值得摩擦。
## 内置模式
| 类别 | 示例 |
|---|---|
| 文件系统毁灭 | `rm -rf /`、`rm -rf ~/*`、`rm -rf /etc` |
| 磁盘手术 | `dd if=… of=/dev/sd*`、`mkfs.*`、`fdisk/parted` |
| 电源/状态 | `shutdown`、`reboot`、`halt`、`init 0/6` |
| 进程击杀 | `kill -9 1`、`pkill -9 -u root` |
| Fork 炸弹 | `:(){ :\|:& };:` |
| 权限洗劫 | `chmod -R 777 /`、`chown -R nobody /` |
| 防火墙关闭 | `iptables -F`、`ufw disable` |
## 确认仪式
```text
⚠ 高危命令
  rm -rf /tmp/build/*
  类别: 递归删除 · 范围: /tmp/build/*

输入 YES 确认:
> yes        ✗ 必须精确输入 YES
> y          ✗ 必须精确输入 YES
> YES        ✔ 执行中
```
精确匹配 `YES`，30 秒超时（`WOW_CONFIRM_TIMEOUT`），没有"本次会话不再询问"。摩擦就是功能。
## 自定义模式
```bash
# ~/.wow-agent.env —— 正则 JSON 数组
WOW_DANGEROUS_PATTERNS='["terraform\\s+destroy", "kubectl\\s+delete\\s+(ns|namespace)"]'
```
用来管你们组织自己的大杀器：带 `--force` 的生产部署、删库、清队列。
## 设计理由
- **为什么不直接禁？** 有些危险命令是合法的（`rm -rf build/`）。防护层把"有风险"和"已确认的高风险"分开。
- **为什么输入 YES 而不是 y/N？** 误按一个键不该授权毁灭。`YES` 需要意图。
- **为什么没有全局跳过？** "总是允许"就是一个疲惫的深夜变成简历事件的元凶。全局策略应该交给[沙盒]（第 1 层）。
## 它拦不住什么
"效果上"有破坏性但看起来无辜的命令（`find … -delete`、迁移脚本里的 `DROP TABLE`）。把这层和[快照与回滚](/zh/safety/rollback/)配对 —— 行为级失误靠数据级恢复兜底。
