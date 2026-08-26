---
title: Dangerous Command Guard
layout: docs
permalink: /safety/dangerous-commands/
eyebrow: Safety · Layer 3
description: Typed-YES confirmation for destructive commands — built-in patterns, custom rules and why confirmation is the last line of defense.
---

Layer 3 catches commands that would destroy data or systems. It is deliberately annoying: these commands deserve friction.

## Built-in patterns

| Class | Examples |
|---|---|
| filesystem destruction | `rm -rf /`, `rm -rf ~/*`, `rm -rf /etc` |
| disk surgery | `dd if=… of=/dev/sd*`, `mkfs.*`, `fdisk/parted` |
| power/state | `shutdown`, `reboot`, `halt`, `init 0/6` |
| process kill | `kill -9 1`, `pkill -9 -u root` |
| fork bombs | `:(){ :\|:& };:` |
| permission wipeout | `chmod -R 777 /`, `chown -R nobody /` |
| firewall disable | `iptables -F`, `ufw disable` |

## The confirmation ritual

```text
⚠ DANGEROUS COMMAND
  rm -rf /tmp/build/*
  class: recursive deletion · scope: /tmp/build/*

Type YES to confirm:
> yes        ✗ must be exactly YES
> y          ✗ must be exactly YES
> YES        ✔ executing
```

Exact-match `YES`, 30-second timeout (`WOW_CONFIRM_TIMEOUT`), no remember-me. Friction is the feature.

## Custom patterns

```bash
# ~/.wow-agent.env — JSON array of regex
WOW_DANGEROUS_PATTERNS='["terraform\\s+destroy", "kubectl\\s+delete\\s+(ns|namespace)"]'
```

Use it for your org's own blunderbusses: prod deploys with `--force`, database drops, queue purges.

## Design rationale

- **Why not just block?** Some dangerous commands are legitimate (`rm -rf build/`). The guard separates *risky* from *confirmed-risky*.
- **Why typed YES, not y/N?** Mis-typing a single key must not authorize destruction. `YES` requires intent.
- **Why no session-wide skip?** "Always allow" is how one tired evening becomes a resume-generating event. The sandbox (Layer 1) is the right place for blanket policy.

## What it can't catch

Commands that are destructive *in effect* but innocent-looking (`find … -delete`, app-level `DROP TABLE` inside a migration). Pair this layer with [snapshots & rollback](/safety/rollback/) — behavior-level mistakes are undone by data-level recovery.
