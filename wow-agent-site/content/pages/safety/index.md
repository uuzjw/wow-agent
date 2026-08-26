---
title: Safety System
layout: docs
permalink: /safety/
eyebrow: Safety
description: Four defensive layers — network sandbox, egress guard, dangerous-command confirmation and rollback.
---

```text
Layer 1 · Network sandbox     unshare -n isolation
Layer 2 · Egress guard        blocks curl POST / scp / git push / npm publish
Layer 3 · Dangerous commands  double confirm rm -rf / dd / fork bombs
Layer 4 · Rollback            /undo + automatic task rollback
```

## Quick check

```bash
/safe status       # sandbox + guard state
/safe logs         # recent events (blocks, confirms, rollbacks)
/safe test         # self-test all layers
```

## Threat model

| Threat | Mitigation |
|---|---|
| data exfiltration | sandbox + egress patterns |
| code theft | local execution + egress guard |
| destructive actions | typed `YES` confirmation |
| broken changes | snapshots + auto rollback |

Safety cannot prevent logic bugs or social engineering — review confirmations before typing `YES`.

Details: [Network Sandbox](/safety/network-sandbox/) · [Rollback](/safety/rollback/)
