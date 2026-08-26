---
title: Network Sandbox
layout: docs
permalink: /safety/network-sandbox/
eyebrow: Safety · Layer 1
description: unshare -n namespace isolation with a proxy-blackhole fallback.
---

## Primary mechanism

The agent runs inside an isolated network namespace:

```bash
unshare -n -- wow-agent
# no interfaces (except loopback), no DNS, no outbound sockets
```

## Fallback

Where `unshare` is unavailable (containers, restricted kernels), a proxy blackhole drops all traffic:

```bash
export WOW_PROXY_BLACKHOLE=1
```

## Allowed vs blocked

| Allowed | Blocked |
|---|---|
| local filesystem | outbound HTTP/HTTPS |
| unix domain sockets | DNS resolution |
| local DB via socket | `git clone`, `pip install`, `ping` |

## Tuning

```bash
WOW_SAFE_MODE=1                 # master switch (default on)
WOW_SANDBOX_ALLOW_PORTS=5432    # allow local postgres
WOW_SANDBOX_ALLOW_LOOPBACK=0    # allow 127.0.0.1 services
```

Verify with `/safe test` — it exercises every layer and prints the result.
