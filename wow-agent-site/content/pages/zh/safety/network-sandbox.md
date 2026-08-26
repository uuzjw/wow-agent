---
title: 断网沙盒
layout: docs
permalink: /zh/safety/network-sandbox/
eyebrow: 安全 · 第 1 层
description: unshare -n 命名空间隔离，不可用时降级代理黑洞。
---

## 主机制

代理运行在隔离的网络命名空间内：

```bash
unshare -n -- wow-agent
# 无网络接口（回环除外）、无 DNS、无出站套接字
```

## 降级方案

`unshare` 不可用时（容器、受限内核），用代理黑洞丢弃全部流量：

```bash
export WOW_PROXY_BLACKHOLE=1
```

## 允许 vs 拦截

| 允许 | 拦截 |
|---|---|
| 本地文件系统 | 出站 HTTP/HTTPS |
| Unix 域套接字 | DNS 解析 |
| 本地数据库（socket） | `git clone`、`pip install`、`ping` |

## 调优

```bash
WOW_SAFE_MODE=1                 # 总开关（默认开启）
WOW_SANDBOX_ALLOW_PORTS=5432    # 放行本地 postgres
WOW_SANDBOX_ALLOW_LOOPBACK=0    # 放行 127.0.0.1 服务
```

运行 `/safe test` 验证 —— 它会逐层测试并输出结果。
